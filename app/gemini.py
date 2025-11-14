# app/gemini.py
import google.generativeai as genai
import json
import logging
from app.core.config import settings
from app.models import Phrase

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro-latest')

async def check_user_translation(original_phrase: Phrase, user_translation: str, direction: str) -> dict:
    source_lang_code, target_lang_code = direction.split('-')
    
    source_text = getattr(original_phrase, f'text_{source_lang_code}')
    target_text = getattr(original_phrase, f'text_{target_lang_code}')
    
    # Промпт адаптирован для лучшего понимания моделью
    prompt = f"""
    Role: AI language tutor.
    Task: Evaluate a user's translation and provide feedback in JSON format.
    
    Context:
    - Original phrase ({source_lang_code}): "{source_text}"
    - Correct translation for reference ({target_lang_code}): "{target_text}"
    - User's translation ({target_lang_code}): "{user_translation}"
    
    Instructions:
    1.  Evaluate the user's translation for grammatical accuracy, spelling, and semantic correctness.
    2.  Provide a score from 0 to 100. 100 is a perfect, natural-sounding translation.
    3.  Provide the best possible correct translation.
    4.  Provide a brief, friendly, and helpful explanation in Russian, pointing out any mistakes. If the translation is perfect, offer praise.
    5.  List the mistake types (e.g., "Spelling, Tense"). If none, leave it as an empty string.
    6.  The entire output MUST be a single JSON object, with no other text before or after it.

    JSON Structure:
    {{
        "score": integer,
        "correct_translation": "string",
        "explanation": "string in Russian",
        "mistakes": "string"
    }}
    
    Now, evaluate the user's translation.
    """
    
    try:
        response = await model.generate_content_async(prompt)
        # Улучшенная очистка ответа
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
        result = json.loads(cleaned_response)
        return result
    except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as e:
        logging.error(f"Gemini response parsing error: {e}\nResponse text: {response.text}")
        return {
            "score": 0,
            "correct_translation": target_text,
            "explanation": "Произошла ошибка при анализе вашего ответа. Попробуйте еще раз.",
            "mistakes": "AI Error"
        }