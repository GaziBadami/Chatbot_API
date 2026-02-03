# Logic for Groq AI (The "Masking" layer with Vision Support)
import os
import base64
from groq import Groq
from dotenv import load_dotenv

# Load variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def encode_image(image_path):
    """Helper to encode local images to base64 for the Vision API."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

# chatbot.py

def get_ai_response(user_message, history):
    VISION_MODELS = [
        "meta-llama/llama-4-scout-17b-16e-instruct", 
        "meta-llama/llama-4-maverick-17b-128e-instruct"
    ]
    # Keep your fallback model as is
    TEXT_MODEL = "llama-3.3-70b-versatile"
    

    try:
        has_image = False
        processed_messages = []
        
        # 1. System Message
        system_content = ("You are Chat-Bot, a custom assistant for Technowire Data Science Ltd. "
                          "You have vision capabilities. If an image is provided, analyze it accurately. "
                          "You also process PDF text provided in the history. "
                          "Never mention OpenAI, Groq, Meta, or Llama. Be professional and concise.")
        
        # 2. Process History and check for images
        for chat in history:
            role = chat['role']
            content = chat['content']
            
            # Check for image triggers 
            if "uploads/" in content and any(ext in content.lower() for ext in [".png", ".jpg", ".jpeg"]):
                filename = content.split("/")[-1].split(")")[0].split("]")[0].strip()
                file_path = os.path.join("uploads", filename)
                
                if os.path.exists(file_path):
                    base64_image = encode_image(file_path)
                    if base64_image:
                        has_image = True
                        processed_messages.append({
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"[User uploaded image: {filename}]"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        })
                        continue 
            
            processed_messages.append({"role": role, "content": content})

        # 3. Add current user message
        processed_messages.append({"role": "user", "content": user_message})

        # 4. Final Formatting for API
        # If has_image is True, ALL messages must use the block format (list of dicts)
        final_messages = [{"role": "system", "content": system_content}]
        for m in processed_messages:
            if has_image:
                # Convert the plain text strings into a list-block format for Vision compatibility
                if isinstance(m["content"], str):
                    final_messages.append({
                        "role": m["role"],
                        "content": [{"type": "text", "text": m["content"]}]
                    })
                else:
                    final_messages.append(m)
            else:
                final_messages.append(m)

        # 5. attempt API Call with the Vision Models first if the image exists
        if has_image:
            for model_name in VISION_MODELS:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=final_messages,
                        temperature=0.7,
                        max_tokens=2048
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    print(f"Vision model {model_name} failed: {e}")
                    continue # Try next vision model

        # 6. Fallback to Text Model (or default if no image) 
        # ensures that the messages are back to the string format for text-only models
        text_messages = [{"role": "system", "content": system_content}]
        for m in processed_messages:
            content = m["content"]
            if isinstance(content, list):
                # Extract the text from the vision block
                content = next((item["text"] for item in content if item["type"] == "text"), "")
            text_messages.append({"role": m["role"], "content": content})

        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=text_messages,
            temperature=0.7,
            max_tokens=2048
        )
        
        reply = response.choices[0].message.content
        if has_image:
            reply += "\n\n(Note: Image processed via text fallback as vision models are currently unavailable.)"
        return reply

    except Exception as e:
        print(f"CRITICAL AI ERROR: {str(e)}")
        return f"AI Error: {str(e)}"