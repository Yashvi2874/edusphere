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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:4173"],
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

def rank_query(query, top_k=5):
    if corpus_embeddings is None:
        return []
    query_embedding = model.encode(query, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=top_k)[0]
    results = []
    for hit in hits:
        folder = folder_names[hit["corpus_id"]]
        score = float(hit["score"])
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

@app.get("/")
async def root():
    return {"message": "Edusphere Chatbot API is running!"}

@app.post("/chat", response_model=List[ChatResponse])
async def chat(request: ChatRequest):
    """Handle chat messages and return AI responses"""
    try:
        # Ensure user exists in database
        db.create_user(request.user_id)
        
        # Get ranked results from RAG
        ranked_results = rank_query(request.message, top_k=3)
        
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
                sources.append({
                    "title": result['folder'].split('/')[-1].replace('_', ' '),
                    "content": result['content'][:200] + "...",
                    "score": result['score'],
                    "path": result['folder']
                })
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
    """Google OAuth login"""
    try:
        # Verify the token with Google
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={request.accessToken}"
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")
            
            token_info = response.json()
            
            # Verify that the token is for the correct user
            if token_info.get("email") != request.email:
                raise HTTPException(status_code=401, detail="Email mismatch")
        
        # Check if user exists, if not create them
        result = db.get_or_create_google_user(request.email, request.name, request.googleId)
        return AuthResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during Google login: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
