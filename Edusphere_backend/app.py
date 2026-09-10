import sys
import asyncio
import os
import re
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from crawl4ai import *
from database import db
from generator import generator
import httpx

# Windows event loop policy
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Initialize FastAPI app
app = FastAPI(title="Edusphere Chatbot API", version="1.0.0")


# The frontend calls /api/chat, /api/login and so on.
#
# In development Vite proxies those and strips the "/api" before they reach
# here. In a deployed build there is no Vite - FastAPI serves the frontend and
# the API from one origin - so the prefix arrives intact and every route would
# 404. Stripping it here means the same fetch paths work in both places, and no
# route definition has to know about it.
@app.middleware("http")
async def strip_api_prefix(request, call_next):
    path = request.scope.get("path", "")
    if path == "/api":
        request.scope["path"] = "/"
    elif path.startswith("/api/"):
        request.scope["path"] = path[4:]
    return await call_next(request)


# In production the frontend is served from this same origin, so no cross-origin
# request happens at all. These entries are for local development, where Vite
# runs on its own port. ALLOWED_ORIGINS can add more without a code change.
_origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:4173"]
_extra = os.getenv("ALLOWED_ORIGINS", "").strip()
if _extra:
    _origins += [o.strip() for o in _extra.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
model = SentenceTransformer('all-MiniLM-L6-v2')
corpus_embeddings = None
folder_names = None
folder_to_content = {}

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    user_id: str
    conversation_id: str

class NewConversationRequest(BaseModel):
    user_id: str

class DeleteConversationRequest(BaseModel):
    user_id: str
    conversation_id: str

class FeedbackRequest(BaseModel):
    message_id: str
    feedback: str
    reason: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class GoogleLoginRequest(BaseModel):
    email: str
    name: str
    googleId: str
    accessToken: str

class ChatResponse(BaseModel):
    text: str
    sources: Optional[List[dict]] = []
    message_id: Optional[str] = None

class ConversationResponse(BaseModel):
    conversation_id: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
    name: Optional[str] = None

# RAG Functions (from original ARISE.py)

extracted_urls = []

async def crawl_sites(urls):
    all_markdown = ""
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            result = await crawler.arun(
                url=url,
                depth=2,
                same_domain=True,
            )
            cleaned = clean_markdown_links(result.markdown)
            all_markdown += f"\n\n# Source: {url}\n\n" + cleaned
    with open("result_combined.md", "w", encoding="utf-8") as f:
        f.write(all_markdown)
    return all_markdown

def clean_markdown_links(text):
    matches = re.findall(r"https?://[^<]*<((https?:/[^>]*)>)", text)
    for full_match, correct_url in matches:
        extracted_urls.append(correct_url)
        text = text.replace(full_match, correct_url)
    return text

def parse_markdown_to_tree(markdown):
    class HeadingNode:
        def __init__(self, level, title, parent=None):
            self.level = level
            self.title = title
            self.content = ""
            self.children = []
            self.parent = parent

    lines = markdown.splitlines()
    root = HeadingNode(0, "root")
    current = root

    for line in lines:
        heading_match = re.match(r'^(#+)\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            node = HeadingNode(level, title)

            while current.level >= level:
                current = current.parent

            current.children.append(node)
            node.parent = current
            current = node
        else:
            current.content += line + "\n"

    return root

def save_tree_to_folders(node, base_path, folder_content_map):
    if node.title != "root":
        folder_name = re.sub(r"[^a-zA-Z0-9_-]", "_", node.title.strip())
        folder_path = base_path / folder_name
        folder_path.mkdir(exist_ok=True)
        with open(folder_path / "content.md", "w", encoding="utf-8") as f:
            f.write(node.content.strip())
        folder_content_map[str(folder_path)] = node.content.strip()
        base_path = folder_path

    for child in node.children:
        save_tree_to_folders(child, base_path, folder_content_map)

async def prepare_rag():
    base_dir = Path("./db")
    
    # Check if db folder exists and has content
    if base_dir.exists() and any(base_dir.iterdir()):
        print("Using existing database structure...")
        folder_content_map = {}
        
        # Read existing content from db folder
        for folder_path in base_dir.rglob("content.md"):
            with open(folder_path, "r", encoding="utf-8") as f:
                content = f.read()
                folder_content_map[str(folder_path.parent)] = content
    else:
        print("Database not found. Crawling websites to create database...")
        urls = [
            "https://kjsce.somaiya.edu/en/admission/btech",
            "https://scholarships.somaiya.edu/en/",
        ]
        content = await crawl_sites(urls)
        tree = parse_markdown_to_tree(content)

        base_dir.mkdir(exist_ok=True)
        folder_content_map = {}
        save_tree_to_folders(tree, base_dir, folder_content_map)

    corpus_embeddings = []
    folder_names = []

    for folder, text in folder_content_map.items():
        if text.strip():  # Only process non-empty content
            emb = model.encode(text, convert_to_tensor=True)
            corpus_embeddings.append(emb)
            folder_names.append(folder)

    global folder_to_content
    folder_to_content = folder_content_map

    if corpus_embeddings:
        return torch.stack(corpus_embeddings), folder_names
    else:
        print("Warning: No content found to create embeddings")
        return None, []

# Cosine similarity below this is noise, not a match.
#
# semantic_search ALWAYS returns top_k results, however badly they match — so an
# unrelated message still comes back with three confident-looking sources. On
# this corpus a genuine hit scores around 0.60 while an unrelated query still
# scrapes ~0.49, so anything under 0.40 is not worth showing a user.
RELEVANCE_FLOOR = 0.40

# Greetings and pleasantries have no answer in an admissions corpus. Retrieving
# for them produces the same confident-looking noise, and "hi" is the first
# thing almost everyone types.
_GREETING = (
    r"(hi+|hey+|hello+|yo|hola|namaste|greetings)"
    r"(\s+(there|everyone|all|team|folks|guys|bot))?"
    r"|good\s*(morning|afternoon|evening|night)"
    r"|how\s*(are\s*you|r\s*u)(\s*doing)?"
    r"|what'?s\s*up|sup"
)
_SIGNOFF = (
    r"thanks?(\s*(a\s*lot|you|so\s*much))?|thank\s*you|thx|ty"
    r"|ok(ay)?|cool|nice|great|awesome|got\s*it"
    r"|bye|goodbye|see\s*(you|ya)|cya"
)

SMALL_TALK = re.compile(
    r"^\s*(" + _GREETING + r"|" + _SIGNOFF + r"|test(ing)?)\s*[!.?]*\s*$",
    re.IGNORECASE,
)
SIGNOFF_ONLY = re.compile(r"^\s*(" + _SIGNOFF + r")\s*[!.?]*\s*$", re.IGNORECASE)


def is_small_talk(message: str) -> bool:
    """True for greetings and pleasantries that no document can answer."""
    return bool(SMALL_TALK.match(message or ""))


def small_talk_reply(message: str) -> str:
    """Answer the pleasantry, then say what this assistant is actually for."""
    capabilities = (
        "I can answer questions about K. J. Somaiya admissions, scholarships, "
        "fees, eligibility and programmes, and I cite the page each answer "
        "came from."
    )
    if SIGNOFF_ONLY.match(message or ""):
        return "Happy to help. " + capabilities
    return "Hello. " + capabilities + " What would you like to know?"


def pretty_title(folder: str) -> str:
    """
    Turn 'db\\B_Tech_admission\\Bachelor_of_Technology\\Important_Dates' into
    'Important Dates'.

    The old version split on '/' only. These paths are built with the OS
    separator, which on Windows is a backslash, so nothing was ever stripped and
    the whole raw path was shown to the user as the source title.
    """
    parts = [p for p in re.split(r"[\\/]+", folder or "") if p and p != "db"]
    if not parts:
        return "Source"
    return parts[-1].replace("_", " ").strip()


def breadcrumb(folder: str) -> str:
    """'B Tech admission › Bachelor of Technology' — the trail above the title."""
    parts = [p for p in re.split(r"[\\/]+", folder or "") if p and p != "db"]
    return " › ".join(p.replace("_", " ").strip() for p in parts[:-1])


def rank_query(query, top_k=5, min_score=RELEVANCE_FLOOR):
    if corpus_embeddings is None:
        return []
    query_embedding = model.encode(query, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=top_k)[0]
    results = []
    for hit in hits:
        score = float(hit["score"])
        if score < min_score:
            continue
        folder = folder_names[hit["corpus_id"]]
        content = folder_to_content.get(folder, "")
        results.append({"folder": folder, "score": score, "content": content})
    return results

# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup"""
    global corpus_embeddings, folder_names
    print("Initializing RAG system...")
    corpus_embeddings, folder_names = await prepare_rag()
    print("RAG system initialized successfully!")

# Where a built frontend lives, if one was copied in (the Docker image does).
# Defined here rather than lower down because the "/" route below needs it, and
# FastAPI matches routes in the order they are declared.
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).parent / "static"))
HAS_FRONTEND = FRONTEND_DIST.is_dir() and (FRONTEND_DIST / "index.html").exists()


@app.get("/")
async def root():
    """
    The app itself when a frontend is built in, otherwise a liveness message.

    This route has to serve index.html itself: it is declared before the
    catch-all at the bottom, and FastAPI takes the first match, so a catch-all
    added later never sees "/".
    """
    if HAS_FRONTEND:
        from fastapi.responses import FileResponse
        return FileResponse(FRONTEND_DIST / "index.html")
    return {"message": "Edusphere Chatbot API is running!"}

@app.post("/chat", response_model=List[ChatResponse])
async def chat(request: ChatRequest):
    """Handle chat messages and return AI responses"""
    try:
        # Ensure user exists in database
        db.create_user(request.user_id)
        
        # Don't search the corpus for "hi" — there is nothing in it to find, and
        # semantic_search would return three unrelated documents anyway.
        small_talk = is_small_talk(request.message)
        ranked_results = [] if small_talk else rank_query(request.message, top_k=3)

        # Get conversation history for context
        history = db.get_conversation_history(request.user_id, request.conversation_id)

        # Format context from ranked results
        context = "\n\n".join([f"Source [{i+1}]: {r['content']}" for i, r in enumerate(ranked_results)])

        # Generate conversational response using LLM
        if ranked_results:
            response_text = await generator.generate_response(
                query=request.message,
                context=context,
                history=history[-5:] # Send last 5 messages for context
            )

            # Format sources for the frontend
            sources = []
            for result in ranked_results:
                content = result['content'].strip()
                sources.append({
                    "title": pretty_title(result['folder']),
                    "breadcrumb": breadcrumb(result['folder']),
                    "content": content[:400] + ("..." if len(content) > 400 else ""),
                    "score": result['score'],
                })
        elif small_talk:
            # Answer the pleasantry, and say what this assistant is actually for.
            response_text = small_talk_reply(request.message)
            sources = []
        else:
            response_text = "I couldn't find relevant information for your query in the college database. Please try rephrasing your question or ask about admission requirements, scholarships, or academic programs."
            sources = []
        
        # Store message in database
        message_id = db.add_message(
            request.user_id, 
            request.conversation_id, 
            request.message, 
            response_text, 
            sources
        )
        
        return [ChatResponse(text=response_text, sources=sources, message_id=message_id)]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/new_conversation", response_model=ConversationResponse)
async def new_conversation(request: NewConversationRequest):
    """Create a new conversation"""
    try:
        # Ensure user exists
        db.create_user(request.user_id)
        
        # Create new conversation
        conversation_id = db.create_conversation(request.user_id)
        
        return ConversationResponse(conversation_id=conversation_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")

@app.get("/history")
async def get_history(user_id: str, conversation_id: str):
    """Get conversation history"""
    try:
        history = db.get_conversation_history(user_id, conversation_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@app.delete("/conversation")
async def delete_conversation(request: DeleteConversationRequest):
    """Delete a conversation"""
    try:
        success = db.delete_conversation(request.user_id, request.conversation_id)
        if success:
            return {"message": "Conversation deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for a message"""
    try:
        success = db.add_feedback(
            request.message_id, 
            request.feedback, 
            request.reason
        )
        if success:
            return {"message": "Feedback submitted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to submit feedback")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@app.get("/faqs")
async def get_faqs(category: str = "student_projects"):
    """Get FAQs for a specific category"""
    try:
        faqs = db.get_faqs(category)
        return {"faqs": faqs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching FAQs: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        stats = db.get_conversation_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.get("/mentors")
async def get_mentors():
    """Get all available mentors"""
    try:
        mentors = db.get_mentors()
        return mentors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching mentors: {str(e)}")

@app.get("/events")
async def get_events():
    """Get upcoming college events"""
    try:
        events = db.get_events()
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")

@app.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """User signup"""
    try:
        result = db.create_user_with_auth(request.email, request.password, request.name)
        return AuthResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during signup: {str(e)}")

@app.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """User login"""
    try:
        result = db.authenticate_user(request.email, request.password)
        return AuthResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

@app.post("/google-login", response_model=AuthResponse)
async def google_login(request: GoogleLoginRequest):
    """
    Sign in with a Google access token.

    The client sends an ACCESS token (@react-oauth/google's useGoogleLogin
    returns access_token). This used to be handed to
    tokeninfo?id_token=... - a different kind of token entirely - so Google
    answered 400 and every Google sign-in failed with "Invalid Google token",
    however correctly the client id was configured.

    An access token is checked by using it: ask Google's userinfo endpoint who
    it belongs to. If the token is invalid or expired, that call fails.

    The identity then comes from GOOGLE's answer, not from the request body.
    The old code trusted the email the client sent and only cross-checked it,
    which meant anyone could have posted somebody else's address and signed in
    as them once the check ahead of it was broken.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {request.accessToken}"},
            )

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired Google token")

        info = response.json()
        email = info.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Google token carries no email")

        # An unverified address on a Google account is not proof of ownership.
        if not info.get("email_verified", False):
            raise HTTPException(status_code=401, detail="Google account email is not verified")

        result = db.get_or_create_google_user(
            email,
            info.get("name") or email.split("@")[0],
            info.get("sub"),
        )
        return AuthResponse(**result)

    except HTTPException:
        # Already a considered response - do not turn a 401 into a 500 below.
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during Google login: {str(e)}")


# ---------------------------------------------------------------------------
# Serve the built frontend, when there is one.
#
# This block is deliberately LAST: a mount at "/" catches every path that no
# earlier route matched, so mounting it above the API would swallow /chat and
# /login. Declared after them, it only ever sees what is left over.
#
# It is also optional. In development the folder does not exist and Vite serves
# the frontend instead, so this is skipped and nothing changes.
# ---------------------------------------------------------------------------
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

if HAS_FRONTEND:
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """
        Hand every unmatched path to index.html.

        The frontend is a single-page app: it does its own routing in the
        browser, so a deep link like /feedback has no file behind it. Returning
        index.html lets the app boot and route the URL itself, instead of the
        404 a plain static server would give.
        """
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")

    print(f"Serving frontend from {FRONTEND_DIST}")
else:
    print("No built frontend found - API only (run Vite separately in development)")


if __name__ == "__main__":
    import uvicorn
    # PORT is what most hosts inject; 5001 keeps local behaviour unchanged.
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5001")))
