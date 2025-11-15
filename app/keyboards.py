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
        'themes': '📚 Mavzular', 'level': '📈 Daraja', 'direction': '🔁 Yo‘nalish',
        'start': '▶ Mashg‘ulotni boshlash', 'profile': '👤 Profil', 'settings': '⚙️ Sozlamalar',
        'next_phrase': '▶️ Keyingi ibora', 'change_topic': '📚 Mavzuni o‘zgartirish', 'change_level': '📈 Darajani o‘zgartirish'
    }
}

# --- Keyboard Functions ---

def language_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора языка интерфейса при первом запуске."""
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇺🇿 O‘zbek", callback_data='lang_uz')],
    ]
    return InlineKeyboardMarkup(keyboard)

def main_menu_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Главное меню с кнопками."""
    texts = button_texts.get(lang, button_texts['ru'])
    keyboard = [
        [texts['themes'], texts['level'], texts['direction']],
        [texts['start']],
        [texts['profile'], texts['settings']]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_dynamic_keyboard(items: list, callback_prefix: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру из списка объектов (например, тем или уровней).
    Автоматически выбирает название на нужном языке (name_ru, name_en, name_uz).
    """
    keyboard = []
    for item in items:
        # Пытаемся получить атрибут name_ru, name_en, name_uz в зависимости от языка.
        # Если такого атрибута нет, по умолчанию используется name_en.
        name = getattr(item, f'name_{lang}', getattr(item, 'name_en', 'N/A'))
        button = InlineKeyboardButton(name, callback_data=f"{callback_prefix}_{item.id}")
        keyboard.append([button])
    return InlineKeyboardMarkup(keyboard)

def direction_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора направления перевода."""
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский → 🇬🇧 Английский", callback_data='dir_ru-en')],
        [InlineKeyboardButton("🇬🇧 Английский → 🇷🇺 Русский", callback_data='dir_en-ru')],
        [InlineKeyboardButton("🇺🇿 O‘zbek → 🇬🇧 Английский", callback_data='dir_uz-en')],
        [InlineKeyboardButton("🇬🇧 Английский → 🇺🇿 O‘zbek", callback_data='dir_en-uz')],
    ]
    return InlineKeyboardMarkup(keyboard)
    
def after_training_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Клавиатура, появляющаяся после проверки перевода."""
    texts = button_texts.get(lang, button_texts['ru'])
    keyboard = [
        [InlineKeyboardButton(texts['next_phrase'], callback_data='next_phrase')],
        [
            InlineKeyboardButton(texts['change_topic'], callback_data='change_topic'),
            InlineKeyboardButton(texts['change_level'], callback_data='change_level')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
