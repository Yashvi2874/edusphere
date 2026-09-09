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
            detail = str(e).lower()

            # Gemini's free tier allows 20 requests a minute. Hitting that is
            # normal during a demo and clears itself in under a minute, so say
            # so rather than making it look like the app is broken.
            if "ratelimit" in detail or "429" in detail or "resource_exhausted" in detail:
                # Plain hyphen, not an em dash: this string is printed to a
                # Windows console in some setups, where a non-ASCII dash comes
                # out as a replacement character.
                return (
                    "I am being rate-limited by the language model right now - the free tier "
                    "allows a limited number of requests per minute. Please ask again in a "
                    "moment. Here is what I found in the meantime:\n\n"
                    f"{context[:500]}..."
                )

            # No key, or a bad one: the retrieval half still works, so make the
            # actual cause obvious instead of hiding it behind a generic message.
            if "api key" in detail or "api_key_invalid" in detail or "401" in detail or "authentication" in detail:
                return (
                    "The language model is not configured, so I cannot write an answer — but I "
                    "did find the relevant pages. Set GEMINI_API_KEY in Edusphere_backend/.env "
                    "to enable written answers.\n\n"
                    f"{context[:500]}..."
                )

            return (
                "I found some information, but I'm having trouble summarizing it right now. "
                f"Here is a snippet: {context[:500]}..."
            )

# Global instance.
# LITELLM_MODEL is documented in .env.template but was never actually read —
# the instance was constructed with no arguments, so the setting did nothing.
generator = LLMGenerator(os.getenv("LITELLM_MODEL", "gemini/gemini-2.5-flash"))
