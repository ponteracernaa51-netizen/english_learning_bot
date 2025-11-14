# app/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# --- Localizations ---
# Тексты для кнопок на разных языках
button_texts = {
    'ru': {
        'themes': '📚 Темы', 'level': '📈 Уровень', 'direction': '🔁 Направление',
        'start': '▶ Начать тренировку', 'profile': '👤 Профиль', 'settings': '⚙️ Настройки',
        'next_phrase': '▶️ Следующая фраза', 'change_topic': '📚 Сменить тему', 'change_level': '📈 Сменить уровень'
    },
    'en': {
        'themes': '📚 Topics', 'level': '📈 Level', 'direction': '🔁 Direction',
        'start': '▶ Start Training', 'profile': '👤 Profile', 'settings': '⚙️ Settings',
        'next_phrase': '▶️ Next Phrase', 'change_topic': '📚 Change Topic', 'change_level': '📈 Change Level'
    },
    'uz': {
        # ... добавьте узбекские переводы
    }
}

# --- Keyboard Functions ---
def language_choice_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
        # [InlineKeyboardButton("🇺🇿 O‘zbek", callback_data='lang_uz')],
    ]
    return InlineKeyboardMarkup(keyboard)

def main_menu_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    texts = button_texts.get(lang, button_texts['ru'])
    keyboard = [
        [texts['themes'], texts['level'], texts['direction']],
        [texts['start']],
        [texts['profile'], texts['settings']]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_dynamic_keyboard(items: list, callback_prefix: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    keyboard = []
    for item in items:
        # В зависимости от языка выбираем нужное поле (name_ru или name_en)
        name = getattr(item, f'name_{lang}', item.name_en) # По умолчанию английский
        button = InlineKeyboardButton(name, callback_data=f"{callback_prefix}_{item.id}")
        keyboard.append([button])
    return InlineKeyboardMarkup(keyboard)

def direction_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский → 🇬🇧 Английский", callback_data='dir_ru-en')],
        [InlineKeyboardButton("🇬🇧 Английский → 🇷🇺 Русский", callback_data='dir_en-ru')],
        # Добавьте другие направления
    ]
    return InlineKeyboardMarkup(keyboard)
    
def after_training_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    texts = button_texts.get(lang, button_texts['ru'])
    keyboard = [
        [InlineKeyboardButton(texts['next_phrase'], callback_data='next_phrase')],
        [
            InlineKeyboardButton(texts['change_topic'], callback_data='change_topic'),
            InlineKeyboardButton(texts['change_level'], callback_data='change_level')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)