import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenRouter API key
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

if openrouter_api_key:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key,
    )
else:
    client = None

def analyze_chinese_image(image_bytes: bytes) -> str:
    """
    Analyzes an image containing Chinese text using OpenRouter API.
    Extracts the Chinese text, provides pinyin, English translation, and a word-by-word breakdown.
    Formats the response cleanly for Telegram.
    
    Args:
        image_bytes (bytes): The bytes of the image to analyze.
        
    Returns:
        str: A cleanly formatted string for Telegram containing the analysis.
    """
    if not client:
        return "⚠️ Error: OPENROUTER_API_KEY not found in .env"

    try:
        # Encode image to base64 for API request
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = (
            "You are an expert Chinese translator and teacher. I have attached an image containing Chinese text.\n\n"
            "Please extract all the Chinese text from the image and provide the following details, formatted clearly for a Telegram message:\n\n"
            "🇨🇳 *Original Text*\n"
            "(The extracted Chinese text here)\n\n"
            "🗣 *Pinyin*\n"
            "(The pinyin corresponding to the text)\n\n"
            "🇬🇧 *English Translation*\n"
            "(The English translation)\n\n"
            "📚 *Word-by-Word Breakdown*\n"
            "• Character/Word (pinyin) - English meaning\n\n"
            "Please keep the text cleanly structured and avoid any characters that might break simple markdown parsing."
        )
        
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error analyzing image with AI: {str(e)}"

def ask_chinese_question(user_question: str) -> str:
    """
    Asks a general question about Chinese language using OpenRouter API.
    
    Args:
        user_question (str): The user's question.
        
    Returns:
        str: The answer from the AI.
    """
    if not client:
        return "⚠️ Error: OPENROUTER_API_KEY not found in .env"

    try:
        response = client.chat.completions.create(
         model="google/gemini-2.0-flash-exp:free",
            messages=[
                {"role": "system", "content": "You are a Chinese language tutor. Answer questions about Chinese words, grammar, pinyin, and meaning. Keep answers concise and beginner-friendly."},
                {"role": "user", "content": user_question}
            ]
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error asking question with AI: {str(e)}"
