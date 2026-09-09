"""
Database module for Edusphere Chatbot
Handles storage of conversations, feedback, and user data
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import bcrypt

# Passwords are stored as bcrypt hashes, never as the password itself.
#
# A hash is one-way: it can confirm a password is correct, but it cannot be
# turned back into the password. So if this file is ever leaked - committed by
# accident, or read off a server - nobody learns anyone's password, and a
# password reused on another site is not compromised.
#
# bcrypt is also deliberately slow, which is what makes guessing millions of
# candidates impractical.
#
# WHY bcrypt DIRECTLY AND NOT passlib: passlib reads bcrypt.__about__.__version__,
# which bcrypt removed in 4.1, so passlib raises AttributeError against any
# current bcrypt. It last shipped a release in 2020. The library's own API is
# two calls, so there is nothing to gain from the wrapper.

# bcrypt hashes at most 72 bytes and silently ignores the rest, which would make
# two long passwords sharing a prefix interchangeable. Rejecting is safer than
# truncating quietly.
_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, stored: str) -> bool:
    """
    True if `password` matches `stored`.

    Accounts created before hashing existed have their password sitting in the
    file as plain text. Those are compared directly so nobody is locked out, and
    the caller then upgrades them - see authenticate_user.
    """
    if not stored:
        return False
    if is_hashed(stored):
        try:
            raw = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
            return bcrypt.checkpw(raw, stored.encode("utf-8"))
        except Exception:
            return False
    return password == stored


def is_hashed(stored: str) -> bool:
    return bool(stored) and stored.startswith(("$2a$", "$2b$", "$2y$"))

class Database:
    def __init__(self, db_path: str = "./data"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        
        # Initialize database files
        self.conversations_file = self.db_path / "conversations.json"
        self.feedback_file = self.db_path / "feedback.json"
        self.users_file = self.db_path / "users.json"
        self.faqs_file = self.db_path / "faqs.json"
        self.mentors_file = self.db_path / "mentors.json"
        self.events_file = self.db_path / "events.json"
        
        # Initialize empty databases if they don't exist
        self._initialize_databases()
    
    def _initialize_databases(self):
        """Initialize empty database files if they don't exist"""
        if not self.conversations_file.exists():
            self._save_json(self.conversations_file, {})
        
        if not self.feedback_file.exists():
            self._save_json(self.feedback_file, {})
        
        if not self.users_file.exists():
            self._save_json(self.users_file, {})
        
        if not self.faqs_file.exists():
            self._save_json(self.faqs_file, {})

        if not self.mentors_file.exists():
            # Seed with some example mentors
            self._save_json(self.mentors_file, {
                "mentor_1": {"name": "Dr. Smith", "subject": "Data Structures", "available": True, "email": "smith@college.edu"},
                "mentor_2": {"name": "Prof. Jane", "subject": "Web Development", "available": True, "email": "jane@college.edu"}
            })

        if not self.events_file.exists():
            # Seed with some example events
            self._save_json(self.events_file, {
                "event_1": {"title": "Hackathon 2026", "date": "2026-06-15", "description": "Annual college hackathon"},
                "event_2": {"title": "Tech Talk: AI", "date": "2026-05-20", "description": "Seminar on Generative AI"}
            })
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path: Path, data: Dict):
        """Save JSON data to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Conversation Management
    def create_conversation(self, user_id: str) -> str:
        """Create a new conversation and return conversation_id"""
        conversations = self._load_json(self.conversations_file)
        
        # Generate unique conversation ID
        conversation_id = f"conv_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if user_id not in conversations:
            conversations[user_id] = {}
        
        conversations[user_id][conversation_id] = {
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "title": "New Conversation"
        }
        
        self._save_json(self.conversations_file, conversations)
        return conversation_id
    
    def add_message(self, user_id: str, conversation_id: str, user_message: str, bot_response: str, sources: List[Dict] = None):
        """Add a message to a conversation"""
        conversations = self._load_json(self.conversations_file)
        
        if user_id in conversations and conversation_id in conversations[user_id]:
            message = {
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "bot_response": bot_response,
                "sources": sources or [],
                "message_id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            }
            
            conversations[user_id][conversation_id]["messages"].append(message)
            self._save_json(self.conversations_file, conversations)
            return message["message_id"]
        return None
    
    def get_conversation_history(self, user_id: str, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        conversations = self._load_json(self.conversations_file)
        
        if user_id in conversations and conversation_id in conversations[user_id]:
            return conversations[user_id][conversation_id]["messages"]
        return []
    
    def get_user_conversations(self, user_id: str) -> Dict[str, Dict]:
        """Get all conversations for a user"""
        conversations = self._load_json(self.conversations_file)
        return conversations.get(user_id, {})
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Delete a conversation"""
        conversations = self._load_json(self.conversations_file)
        
        if user_id in conversations and conversation_id in conversations[user_id]:
            del conversations[user_id][conversation_id]
            self._save_json(self.conversations_file, conversations)
            return True
        return False
    
    # Feedback Management
    def add_feedback(self, message_id: str, feedback: str, reason: str = None, user_id: str = None) -> bool:
        """Add feedback for a message"""
        feedback_data = self._load_json(self.feedback_file)
        
        feedback_entry = {
            "message_id": message_id,
            "feedback": feedback,
            "reason": reason,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if message_id not in feedback_data:
            feedback_data[message_id] = []
        
        feedback_data[message_id].append(feedback_entry)
        self._save_json(self.feedback_file, feedback_data)
        return True
    
    def get_feedback(self, message_id: str) -> List[Dict]:
        """Get feedback for a specific message"""
        feedback_data = self._load_json(self.feedback_file)
        return feedback_data.get(message_id, [])
    
    def get_all_feedback(self) -> Dict:
        """Get all feedback data"""
        return self._load_json(self.feedback_file)
    
    # User Management
    def create_user(self, user_id: str, user_data: Dict = None) -> bool:
        """Create a new user"""
        users = self._load_json(self.users_file)
        
        if user_id not in users:
            users[user_id] = {
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "preferences": {},
                **(user_data or {})
            }
            self._save_json(self.users_file, users)
            return True
        return False
    
    def create_user_with_auth(self, email: str, password: str, name: str = None) -> Dict:
        """Create a new user with authentication"""
        users = self._load_json(self.users_file)
        
        # Check if user already exists
        for user_id, user_data in users.items():
            if user_data.get("email") == email:
                return {"success": False, "message": "User already exists"}
        
        # Create new user
        user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        users[user_id] = {
            "email": email,
            "password": hash_password(password),
            "name": name or email.split('@')[0],
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "preferences": {},
            "is_authenticated": True
        }
        
        self._save_json(self.users_file, users)
        return {"success": True, "user_id": user_id, "name": name or email.split('@')[0], "message": "User created successfully"}
    
    def authenticate_user(self, email: str, password: str) -> Dict:
        """Authenticate user login"""
        users = self._load_json(self.users_file)
        
        for user_id, user_data in users.items():
            if user_data.get("email") != email:
                continue
            stored = user_data.get("password", "")
            if not verify_password(password, stored):
                continue

            # Upgrade an old plain-text password to a hash on the next correct
            # login. This is the only moment the password is available to hash,
            # so old accounts convert themselves as people sign in.
            if not is_hashed(stored):
                user_data["password"] = hash_password(password)

            user_data["last_active"] = datetime.now().isoformat()
            self._save_json(self.users_file, users)
            return {
                "success": True,
                "user_id": user_id,
                "name": user_data.get("name"),
                "message": "Login successful"
            }
        
        return {"success": False, "message": "Invalid email or password"}
    
    def update_user(self, user_id: str, user_data: Dict) -> bool:
        """Update user data"""
        users = self._load_json(self.users_file)
        
        if user_id in users:
            users[user_id].update(user_data)
            users[user_id]["last_active"] = datetime.now().isoformat()
            self._save_json(self.users_file, users)
            return True
        return False
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user data"""
        users = self._load_json(self.users_file)
        return users.get(user_id)
    
    def get_or_create_google_user(self, email: str, name: str, google_id: str) -> Dict:
        """Get existing user or create new user with Google authentication"""
        users = self._load_json(self.users_file)
        
        # Check if user already exists (by email or Google ID)
        for user_id, user_data in users.items():
            if user_data.get("email") == email or user_data.get("google_id") == google_id:
                # Update last active
                user_data["last_active"] = datetime.now().isoformat()
                # Update name if provided
                if name and user_data.get("name") != name:
                    user_data["name"] = name
                self._save_json(self.users_file, users)
                return {
                    "success": True, 
                    "user_id": user_id, 
                    "name": user_data.get("name"),
                    "message": "Login successful"
                }
        
        # Create new user
        user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        users[user_id] = {
            "email": email,
            "name": name,
            "google_id": google_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "preferences": {},
            "is_authenticated": True
        }
        
        self._save_json(self.users_file, users)
        return {"success": True, "user_id": user_id, "name": name, "message": "User created successfully"}

    # FAQ Management
    def get_faqs(self, category: str = "student_projects") -> List[str]:
        """Get FAQs for a specific category"""
        faqs_data = self._load_json(self.faqs_file)
        
        # Default FAQs if not found in database
        default_faqs = {
            "student_projects": [
                "What are the admission requirements for B.Tech?",
                "How do I apply for scholarships?",
                "What is the fee structure for B.Tech?",
                "What are the eligibility criteria for admission?",
                "How can I get financial aid?",
                "What documents are required for admission?",
                "What is the admission process timeline?",
                "Are there any entrance exams required?"
            ],
            "faculty_dashboards": [
                "What courses are offered?",
                "What is the curriculum structure?",
                "What are the faculty qualifications?",
                "What research opportunities are available?",
                "What are the lab facilities?",
                "What is the grading system?",
                "Are there internship opportunities?",
                "What are the placement statistics?"
            ],
            "admissions_info": [
                "What are the admission requirements for B.Tech?",
                "What is the admission process?",
                "What documents are required?",
                "What is the fee structure?",
                "Are there any entrance exams?",
                "What are the eligibility criteria?",
                "How do I apply online?",
                "What is the admission timeline?"
            ],
            "training_and_placement_office_(tpo)": [
                "What are the placement statistics?",
                "Are there internship opportunities?",
                "What companies visit for placements?",
                "How can I prepare for interviews?",
                "What is the average salary package?",
                "What are the placement criteria?",
                "How do I register for placements?",
                "What training programs are available?"
            ],
            "admission": [
                "What are the admission requirements for B.Tech?",
                "What is the admission process?",
                "What documents are required?",
                "What is the fee structure?",
                "Are there any entrance exams?",
                "What are the eligibility criteria?",
                "How do I apply online?",
                "What is the admission timeline?"
            ],
            "scholarships": [
                "How do I apply for scholarships?",
                "What scholarships are available?",
                "What are the eligibility criteria for scholarships?",
                "How can I get financial aid?",
                "What documents are needed for scholarship application?",
                "When is the scholarship application deadline?",
                "Are there merit-based scholarships?",
                "How much financial aid can I get?"
            ],
            "academics": [
                "What courses are offered?",
                "What is the curriculum structure?",
                "What are the faculty qualifications?",
                "What research opportunities are available?",
                "What are the lab facilities?",
                "What is the grading system?",
                "Are there internship opportunities?",
                "What are the placement statistics?"
            ]
        }
        
        # Return FAQs from database or default
        if category in faqs_data:
            return faqs_data[category]
        else:
            return default_faqs.get(category, default_faqs["student_projects"])
    
    def add_faq(self, category: str, question: str) -> bool:
        """Add a new FAQ to a category"""
        faqs_data = self._load_json(self.faqs_file)
        
        if category not in faqs_data:
            faqs_data[category] = []
        
        if question not in faqs_data[category]:
            faqs_data[category].append(question)
            self._save_json(self.faqs_file, faqs_data)
            return True
        return False
    
    # College Connect Features
    def get_mentors(self) -> Dict:
        """Get all mentors"""
        return self._load_json(self.mentors_file)
    
    def get_events(self) -> Dict:
        """Get all events"""
        return self._load_json(self.events_file)

    def get_conversation_stats(self) -> Dict:
        """Get conversation statistics"""
        conversations = self._load_json(self.conversations_file)
        feedback_data = self._load_json(self.feedback_file)
        
        total_conversations = sum(len(user_convs) for user_convs in conversations.values())
        total_messages = sum(
            len(conv["messages"]) 
            for user_convs in conversations.values() 
            for conv in user_convs.values()
        )
        total_feedback = sum(len(feedbacks) for feedbacks in feedback_data.values())
        
        return {
            "total_users": len(conversations),
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_feedback": total_feedback
        }

# Global database instance
db = Database()
