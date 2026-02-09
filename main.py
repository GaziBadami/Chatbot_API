"""
main.py
Core app — /chat, /upload endpoints
Registers frontend (api.py) and admin (admin_api.py) routers
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from database import store_message, get_chat_history
from chatbot import get_ai_response
from database_Conv import ensure_active_conversation, update_label_if_default
import uvicorn
import os
import shutil
import fitz  # PyMuPDF
import base64
from uuid import uuid4
from docx import Document
from uuid import uuid4
from typing import Optional
from spire.doc import Document as SpireDocument

# Import routers
from api import router as conversations_router          # Frontend sidebar routes
from admin_api import router as admin_router            # Admin routes

app = FastAPI(title="Technowire AI Assistant")

# ============================================
# SETUP
# ============================================

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(conversations_router)   # /conversations/...
app.include_router(admin_router)           # /admin/...


# ============================================
# REQUEST MODELS
# ============================================

class ChatRequest(BaseModel):
    user_id: Optional[str] = None
    message: str
    conversation_id: int = None  # Frontend can optionally pass this


# ============================================
# HELPER FUNCTIONS
# ============================================

def extract_text_from_pdf(file_path):
    """Extracts text content from a PDF file."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None

def extract_text_from_word(file_path):
    """Extracts text from .doc and .docx files."""
    try:
        if file_path.endswith(".docx"):
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        doc = SpireDocument()
        doc.LoadFromFile(file_path)
        text = doc.GetText()
        doc.Close()
        return text
    except Exception as e:
        print(f"Error extracting Word text: {e}")
        return ""

def extract_text_from_plain_file(file_path):
    """Extracts text from .txt, .json, .csv, .py files."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"Text Extraction Error: {e}")
        return None

def generate_chat_label(user_message: str, ai_reply: str) -> str:
    """
    Auto-generate a short chat title from the first message
    Uses Groq to create a 4-5 word title
    Falls back to first 40 chars of user message if Groq fails
    """
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Generate a very short title (3-5 words max) for this conversation. Return ONLY the title, nothing else. No quotes, no punctuation."
                },
                {
                    "role": "user",
                    "content": f"User said: {user_message[:200]}\nAssistant replied: {ai_reply[:200]}"
                }
            ],
            temperature=0.3,
            max_tokens=20
        )

        label = response.choices[0].message.content.strip()
        # Safety: if Groq returns something too long, truncate
        return label[:50] if label else user_message[:40]

    except Exception as e:
        print(f"Auto-label generation failed: {e}")
        # Fallback: use first 40 chars of user message
        return user_message[:40]


# ============================================
# ROOT
# ============================================

@app.get("/")
async def root():
    return {"status": "online", "message": "Technowire Z-Bot API is running. Use /docs for API testing."}


# ============================================
# CHAT ENDPOINT
# ============================================

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    Flow:
    1. Ensure active conversation exists
    2. Store user message with conversation_id
    3. Get AI reply
    4. Store AI reply with conversation_id
    5. Auto-generate label if still 'New Chat'
    """
    try:
        # Get or create active conversation
        user_id = request.user_id or f"guest_{uuid4().hex[:8]}"
        active_conv = ensure_active_conversation(request.user_id)
        conversation_id = active_conv['id']

        # Store user message → linked to conversation
        store_message(request.user_id, "user", request.message, conversation_id)

        # Get history from THIS conversation only
        history = get_chat_history(user_id, conversation_id=conversation_id, limit=15)

        # Get AI response
        ai_reply = get_ai_response(request.message, history)

        # Store AI reply → linked to conversation
        store_message(user_id, "assistant", ai_reply, conversation_id)

        # Auto-label: if label is still "New Chat", generate a title
        # Only runs once per conversation (when label is default)
        if active_conv.get('label') == 'New Chat':
            new_label = generate_chat_label(request.message, ai_reply)
            update_label_if_default(conversation_id, new_label)

        return {
            "status": "success",
            "reply": ai_reply,
            "conversation_id": conversation_id,
            "user_id": user_id
        }
    except Exception as e:
        print("CHAT ERROR:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ============================================
# UPLOAD ENDPOINT
# ============================================

@app.post("/upload")
async def upload_file(user_id: str = Form(...), file: UploadFile = File(...)):
    """
    File upload endpoint
    Stores file context as a message linked to active conversation
    """
    try:
        # Ensure active conversation
        active_conv = ensure_active_conversation(user_id)
        conversation_id = active_conv['id']

        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_url = f"http://127.0.0.1:8000/uploads/{unique_filename}"

        # --- PDF ---
        if file_extension == ".pdf":
            pdf_text = extract_text_from_pdf(file_path)
            if pdf_text:
                context_msg = (
                    f"BACKGROUND_DATA: The user has uploaded a file named {file.filename}. "
                    f"Content summary: {pdf_text[:2000]}. Use this info ONLY if asked."
                )
                store_message(user_id, "user", context_msg, conversation_id)

        # --- Word Document ---
        elif file_extension in [".doc", ".docx"]:
            word_text = extract_text_from_word(file_path)
            if word_text:
                context_msg = f"SYSTEM: User uploaded a Word doc: {file.filename}. Content: {word_text[:2000]}"
                store_message(user_id, "user", context_msg, conversation_id)

        # --- Images ---
        elif file_extension in [".jpg", ".jpeg", ".png"]:
            context_msg = f"SYSTEM: User uploaded an image: {file.filename}. (The image is accessible at {file_url})"
            store_message(user_id, "user", context_msg, conversation_id)

        # --- Text / JSON / CSV / Python ---
        elif file_extension in [".json", ".txt", ".csv", ".py"]:
            extracted_content = extract_text_from_plain_file(file_path)
            if extracted_content:
                context_msg = f"BACKGROUND_DATA: Content of {file.filename}:\n{extracted_content[:2000]}"
                store_message(user_id, "user", context_msg, conversation_id)

        # Visible log message in chat
        store_message(user_id, "user", f"[File Uploaded: {file.filename}]", conversation_id)

        return {
            "status": "success",
            "file_url": file_url,
            "conversation_id": conversation_id,
            "message": f"I've received {file.filename}. Note: If I can't see the image content yet, please describe what you need me to analyze in it!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)