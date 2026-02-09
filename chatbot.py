import os
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define models at module level
VISION_MODELS = [
    "llama-3.2-90b-vision-preview",  # Use actual Groq vision model
]
TEXT_MODEL = "llama-3.3-70b-versatile"

def encode_image(image_path):
    """Helper to encode local images to base64 for the Vision API."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def get_ai_response(user_message, history):
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
        final_messages = [{"role": "system", "content": system_content}]
        for m in processed_messages:
            if has_image:
                if isinstance(m["content"], str):
                    final_messages.append({
                        "role": m["role"],
                        "content": [{"type": "text", "text": m["content"]}]
                    })
                else:
                    final_messages.append(m)
            else:
                final_messages.append(m)

        # 5. Use vision model if image exists
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
                    continue

        # 6. Fallback to Text Model
        text_messages = [{"role": "system", "content": system_content}]
        for m in processed_messages:
            content = m["content"]
            if isinstance(content, list):
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
