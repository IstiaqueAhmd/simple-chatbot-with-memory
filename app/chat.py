from openai import OpenAI
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class FitnessChat:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_prompt = """You are a knowledgeable fitness and health assistant. You provide helpful, 
        accurate, and motivating advice about:
        - Exercise routines and workout plans
        - Nutrition and diet recommendations
        - Health and wellness tips
        - Injury prevention and recovery
        - Mental health and motivation
        
        Always provide safe, evidence-based advice and recommend consulting healthcare professionals 
        for serious health concerns. Be encouraging and supportive in your responses."""
    
    def generate_response(self, message: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """Generate a response using OpenAI API"""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add the current user message
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}. Please try again."
    
    def get_conversation_context(self, messages: List[Dict[str, str]], max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation context for API calls"""
        return messages[-max_messages:] if len(messages) > max_messages else messages