# app/gemini.py

import google.generativeai as genai
import json
import logging
from google.api_core import exceptions as google_exceptions
from app.core.config import settings
from app.models import Phrase

# Конфигурируем API с вашим ключом
genai.configure(api_key=settings.GEMINI_API_KEY)

# --- Выбор модели ---
# Рекомендуется использовать 'gemini-1.5-flash-latest'.
# Это самая быстрая и экономичная модель, идеально подходящая для чат-бота.
# Если она не работает, убедитесь, что вы обновили библиотеку:
# pip install --upgrade google-generativeai
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Настройка для генерации контента, которая просит модель СТРОГО придерживаться JSON
generation_config = genai.GenerationConfig(
    response_mime_type="application/json",
)


async def check_user_translation(original_phrase: Phrase, user_translation: str, direction: str) -> dict:
    """
    Обращается к Gemini API для оценки перевода пользователя.
    В случае ошибки API пробрасывает исключение наверх для обработки в хэндлере.
    """
    source_lang_code, target_lang_code = direction.split('-')
    
    source_text = getattr(original_phrase, f'text_{source_lang_code}')
    target_text = getattr(original_phrase, f'text_{target_lang_code}')
    
    # Промпт адаптирован для лучшего понимания моделью и принудительного вывода в JSON
    prompt = f"""
    Role: AI language tutor.
    Task: Evaluate a user's translation and provide feedback.
    
    Context:
    - Original phrase ({source_lang_code}): "{source_text}"
    - Correct translation for reference ({target_lang_code}): "{target_text}"
    - User's translation ({target_lang_code}): "{user_translation}"
    
    Instructions:
    1.  Evaluate the user's translation for grammatical accuracy, spelling, and semantic correctness.
    2.  Provide a score from 0 to 100. 100 is a perfect, natural-sounding translation.
    3.  Provide the best possible correct translation.
    4.  Provide a brief, friendly, and helpful explanation in Russian, pointing out any mistakes. If the translation is perfect, offer praise.
    5.  List the mistake types as a string (e.g., "Spelling, Tense"). If there are no mistakes, use an empty string "".

    Your entire output MUST be a valid JSON object matching this structure:
    {{
        "score": integer,
        "correct_translation": "string",
        "explanation": "string in Russian",
        "mistakes": "string"
    }}
    """
    
    try:
        # Используем асинхронный вызов и передаем конфигурацию для JSON
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        # Модель с `response_mime_type="application/json"` должна возвращать чистый JSON,
        # но на всякий случай оставим очистку от возможных маркеров.
        cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
        result = json.loads(cleaned_response)
        return result

    except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as e:
        # Ошибка, если модель вернула невалидный JSON или вообще не JSON
        response_text = getattr(response, 'text', 'No response text available')
        logging.error(f"Gemini response parsing error: {e}\nResponse text: {response_text}")
        # Пробрасываем ошибку наверх, чтобы обработчик мог ее поймать и сообщить пользователю
        raise ValueError("AI response parsing failed")

    except google_exceptions.ResourceExhausted as e:
        # Ошибка превышения квоты (429 Too Many Requests)
        logging.error(f"Gemini API quota exceeded: {e}")
        # Пробрасываем ошибку наверх для корректной обработки в `training.py`
        raise e
