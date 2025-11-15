# app/gemini.py (ПОЛНАЯ ВЕРСИЯ)

import google.generativeai as genai
import json
import logging
from google.api_core import exceptions as google_exceptions
from app.core.config import settings
from app.models import Phrase, User # <-- Импортируем User

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

async def check_user_translation(original_phrase: Phrase, user_translation: str, user: User) -> dict:
    """
    Обращается к Gemini API для оценки перевода пользователя на его языке.
    """
    direction = user.direction
    user_lang = user.language

    # Словарь для локализации промпта
    lang_map = {
        'ru': 'Russian',
        'en': 'English',
        'uz': 'Uzbek'
    }
    feedback_lang = lang_map.get(user_lang, 'Russian') # По умолчанию русский

    source_lang_code, target_lang_code = direction.split('-')
    
    source_text = getattr(original_phrase, f'text_{source_lang_code}')
    target_text = getattr(original_phrase, f'text_{target_lang_code}')
    
    prompt = f"""
    Role: AI language tutor.
    Task: Evaluate a user's translation and provide feedback.
    
    Context:
    - Original phrase ({source_lang_code}): "{source_text}"
    - Correct translation for reference ({target_lang_code}): "{target_text}"
    - User's translation ({target_lang_code}): "{user_translation}"
    
    Instructions:
    1.  Evaluate the user's translation for accuracy.
    2.  Provide a score from 0 to 100.
    3.  Provide the best possible correct translation.
    4.  Provide a brief, friendly, and helpful explanation in {feedback_lang}. If the translation is perfect, offer praise in {feedback_lang}.
    5.  List mistake types as a string (e.g., "Spelling, Tense"). If none, use an empty string "".

    Your entire output MUST be a valid JSON object matching this structure:
    {{
        "score": integer,
        "correct_translation": "string",
        "explanation": "string in {feedback_lang}",
        "mistakes": "string"
    }}
    """
    
    try:
        response = await model.generate_content_async(prompt)
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
        result = json.loads(cleaned_response)
        return result

    except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as e:
        response_text = getattr(response, 'text', 'No response text available')
        logging.error(f"Gemini response parsing error: {e}\nResponse text: {response_text}")
        raise ValueError("AI response parsing failed")

    except google_exceptions.ResourceExhausted as e:
        logging.error(f"Gemini API quota exceeded: {e}")
        raise e
