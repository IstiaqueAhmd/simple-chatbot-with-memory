from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from database import get_db
from schema import ChatRequest, ChatResponse, ChatHistory, SessionList, ChatSession
from chat import Chat
from utils import (
    create_chat_session, 
    save_message, 
    get_chat_history, 
    get_user_sessions,
    delete_chat_session,
    update_session_title
)

# Create FastAPI app
app = FastAPI(
    title="Fitness Chat API",
    description="A fitness-focused chat API powered by AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chat service
chat = Chat()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Fitness Chat API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message and get AI response"""
    try:
        session_id = request.session_id
        
        # Create new session if none provided
        if not session_id:
            session_id = create_chat_session(db, request.user_id)
        
        # Get conversation history
        history = get_chat_history(db, session_id)
        
        # Save user message
        save_message(db, session_id, "user", request.message)
        
        # Generate AI response
        ai_response = chat.generate_response(request.message, history)
        
        # Save AI response
        save_message(db, session_id, "assistant", ai_response)
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )

@app.post("/sessions", response_model=dict)
async def create_session(user_id: str = "anonymous", title: str = "New Chat", db: Session = Depends(get_db)):
    """Create a new chat session"""
    try:
        session_id = create_chat_session(db, user_id, title)
        return {"session_id": session_id, "message": "Session created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )

@app.get("/sessions/{user_id}", response_model=SessionList)
async def get_sessions(user_id: str, db: Session = Depends(get_db)):
    """Get all chat sessions for a user"""
    try:
        sessions = get_user_sessions(db, user_id)
        return SessionList(sessions=sessions)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sessions: {str(e)}"
        )

@app.get("/chat/{session_id}/history", response_model=ChatHistory)
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    """Get chat history for a specific session"""
    try:
        messages = get_chat_history(db, session_id)
        chat_messages = [
            {"role": msg["role"], "content": msg["content"], "timestamp": datetime.utcnow()}
            for msg in messages
        ]
        return ChatHistory(session_id=session_id, messages=chat_messages)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat history: {str(e)}"
        )

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str, db: Session = Depends(get_db)):
    """Delete a chat session"""
    try:
        success = delete_chat_session(db, session_id, user_id)
        if success:
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting session: {str(e)}"
        )

@app.put("/sessions/{session_id}/title")
async def update_title(session_id: str, title: str, user_id: str, db: Session = Depends(get_db)):
    """Update session title"""
    try:
        success = update_session_title(db, session_id, user_id, title)
        if success:
            return {"message": "Title updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating title: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)