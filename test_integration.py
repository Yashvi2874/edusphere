#!/usr/bin/env python3
"""
Test script to verify the Edusphere chatbot integration
"""
import requests
import json
import time

def test_backend_health():
    """Test if the backend is running and healthy"""
    try:
        response = requests.get("http://localhost:5001/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not accessible: {e}")
        return False

def test_new_conversation():
    """Test creating a new conversation"""
    try:
        response = requests.post(
            "http://localhost:5001/new_conversation",
            json={"user_id": "test_user"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            conversation_id = data.get("conversation_id")
            print(f"✅ New conversation created: {conversation_id}")
            return conversation_id
        else:
            print(f"❌ Failed to create conversation: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating conversation: {e}")
        return None

def test_chat_message(conversation_id):
    """Test sending a chat message"""
    try:
        response = requests.post(
            "http://localhost:5001/chat",
            json={
                "message": "What is the admission process for B.Tech?",
                "user_id": "test_user",
                "conversation_id": conversation_id
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                bot_response = data[0].get("text", "")
                sources = data[0].get("sources", [])
                print(f"✅ Chat message sent successfully")
                print(f"   Response: {bot_response[:100]}...")
                print(f"   Sources: {len(sources)} found")
                return True
            else:
                print("❌ Empty response from chat endpoint")
                return False
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending chat message: {e}")
        return False

def test_chat_history(conversation_id):
    """Test retrieving chat history"""
    try:
        response = requests.get(
            "http://localhost:5001/history",
            params={"user_id": "test_user", "conversation_id": conversation_id},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat history retrieved: {len(data)} messages")
            return True
        else:
            print(f"❌ Failed to retrieve chat history: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving chat history: {e}")
        return False

def main():
    print("Testing Edusphere Chatbot Integration")
    print("=" * 50)
    
    # Test 1: Backend health
    if not test_backend_health():
        print("\n❌ Backend is not running. Please start the backend first:")
        print("   cd Edusphere_backend && python start_backend.py")
        return
    
    # Test 2: Create conversation
    conversation_id = test_new_conversation()
    if not conversation_id:
        print("\n❌ Failed to create conversation. Integration test failed.")
        return
    
    # Test 3: Send chat message
    if not test_chat_message(conversation_id):
        print("\n❌ Failed to send chat message. Integration test failed.")
        return
    
    # Test 4: Retrieve chat history
    if not test_chat_history(conversation_id):
        print("\n❌ Failed to retrieve chat history. Integration test failed.")
        return
    
    print("\nAll integration tests passed!")
    print("✅ Backend and frontend should work together correctly.")
    print("\nNext steps:")
    print("1. Start the frontend: cd Edusphere_frontend && npm run dev")
    print("2. Open http://localhost:5173 in your browser")
    print("3. Test the chatbot interface")

if __name__ == "__main__":
    main()

