import axios from 'axios';

// Prefer Vite dev proxy ("/api") by default; allow override via env
const BACKEND_URL = import.meta?.env?.VITE_BACKEND_URL || '/api';

export async function askBot(question, userId, conversationId) {
  try {
    const res = await axios.post(`${BACKEND_URL}/chat`, { 
      message: question,
      user_id: userId,
      conversation_id: conversationId
    });
    return res.data;
  } catch (error) {
    console.error("Backend Error:", error);
    return [{ text: "Sorry, something went wrong.", sources: [] }];
  }
}

export async function createNewConversation(userId) {
  try {
    const res = await axios.post(`${BACKEND_URL}/new_conversation`, { 
      user_id: userId
    });
    return res.data;
  } catch (error) {
    console.error("Error creating conversation:", error);
    throw error;
  }
}

export async function getChatHistory(userId, conversationId) {
  try {
    const res = await axios.get(`${BACKEND_URL}/history`, {
      params: { user_id: userId, conversation_id: conversationId }
    });
    return res.data;
  } catch (error) {
    console.error("Error fetching history:", error);
    return [];
  }
}

export async function deleteConversation(userId, conversationId) {
  try {
    const res = await axios.delete(`${BACKEND_URL}/conversation`, {
      data: { user_id: userId, conversation_id: conversationId }
    });
    return res.data;
  } catch (error) {
    console.error("Error deleting conversation:", error);
    throw error;
  }
}

export async function submitFeedback(messageId, feedback, reason = null) {
  try {
    console.log('Submitting feedback:', { messageId, feedback, reason });
    const res = await axios.post(`${BACKEND_URL}/feedback`, {
      message_id: messageId,
      feedback: feedback,
      reason: reason
    });
    console.log('Feedback response:', res.data);
    return res.data;
  } catch (error) {
    console.error("Error submitting feedback:", error);
    if (error.response) {
      console.error("Response data:", error.response.data);
      console.error("Response status:", error.response.status);
    }
    throw error;
  }
}

export async function getFAQs(category = 'generic') {
  try {
    const res = await axios.get(`${BACKEND_URL}/faqs`, {
      params: { category: category }
    });
    return res.data;
  } catch (error) {
    console.error("Error fetching FAQs:", error);
    return { faqs: [] };
  }
}

export async function signup(email, password, name = null) {
  try {
    const res = await axios.post(`${BACKEND_URL}/signup`, {
      email: email,
      password: password,
      name: name
    });
    return res.data;
  } catch (error) {
    console.error("Error during signup:", error);
    throw error;
  }
}

export async function login(email, password) {
  try {
    const res = await axios.post(`${BACKEND_URL}/login`, {
      email: email,
      password: password
    });
    return res.data;
  } catch (error) {
    console.error("Error during login:", error);
    throw error;
  }
}
