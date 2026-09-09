import os
import litellm
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMGenerator:
    # gemini-1.5-flash was retired and now 404s, which is what made every answer
    # fall back to the raw snippet. Keep this default current, and let .env win.
    def __init__(self, model_name: str = "gemini/gemini-2.5-flash"):
        self.model_name = model_name
        # Ensure API keys are set or handle appropriately
        # litellm will look for GEMINI_API_KEY, OPENAI_API_KEY, etc.
        
    async def generate_response(
        self, 
        query: str, 
        context: str, 
        history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate a conversational response based on query and retrieved context.
        """
        if not context:
            return "I'm sorry, I couldn't find any specific information in our records to answer that accurately. Could you try rephrasing your question?"

        system_prompt = (
            "You are the Edusphere Assistant, a helpful and professional academic advisor. "
            "Your goal is to answer student questions accurately based ONLY on the provided context. "
            "If the answer is not in the context, politely say you don't know and suggest who to contact. "
            "Keep your tone encouraging and professional. "
            "Use markdown formatting for clarity (bullet points, bold text).\n\n"
            f"CONTEXT:\n{context}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history if available
        if history:
            for msg in history:
                messages.append({"role": "user", "content": msg["user_message"]})
                messages.append({"role": "assistant", "content": msg["bot_response"]})

        messages.append({"role": "user", "content": query})

        try:
            response = await litellm.acompletion(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in LLM generation: {str(e)}")
            return f"I found some information, but I'm having trouble summarizing it right now. Here is a snippet: {context[:500]}..."

# Global instance.
# LITELLM_MODEL is documented in .env.template but was never actually read —
# the instance was constructed with no arguments, so the setting did nothing.
generator = LLMGenerator(os.getenv("LITELLM_MODEL", "gemini/gemini-2.5-flash"))
