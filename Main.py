import sqlite3
import telebot
from telebot import types
import requests
import logging
import time
from urllib.parse import quote

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8601649522:AAFbXAaEX2QAL6iwn8BXtpdCn-aqDh9IkaY"
ADMIN_ID = 8727723180
MANAGER_USERNAME = "@username_vladelca"

# ==================== НАСТРОЙКА ЛОГИРОВАНИЯ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('errors.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== ФУНКЦИЯ ПЕРЕВОДА ====================
def translate_to_belarusian(text):
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "ru|be", "de": "demo@example.com"}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        return data["responseData"]["translatedText"]
    except Exception as error:
        logger.error(f"Ошибка перевода: {error}")
        return text

# ==================== БАЗА ДАННЫХ ====================
def get_database_connection():
    connection = sqlite3.connect("shop.db", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database():
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ru TEXT NOT NULL,
                name_by TEXT NOT NULL,
                description_ru TEXT DEFAULT '',
                description_by TEXT DEFAULT '',
                price REAL NOT NULL,
                category_ru TEXT NOT NULL,
                category_by TEXT NOT NULL,
                in_stock INTEGER DEFAULT 1,
                attributes_ru TEXT DEFAULT '',
                attributes_by TEXT DEFAULT '',
                photo_id TEXT DEFAULT ''
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_ru TEXT NOT NULL,
                text_by TEXT NOT NULL,
                active INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ru'
            )
        """)
        
        connection.commit()
        logger.info("База данных инициализирована успешно")
    except Exception as error:
        logger.error(f"Ошибка инициализации БД: {error}")
    finally:
        connection.close()

# ==================== CRUD ОПЕРАЦИИ ====================
def add_product_to_database(name_ru, name_by, price, category_ru, category_by, description_ru='', description_by='', attributes_ru='', attributes_by='', photo_id=''):
    try:
        connection = get_database_connection()
        connection.execute("""
            INSERT INTO products (name_ru, name_by, description_ru, description_by, price, category_ru, category_by, attributes_ru, attributes_by, photo_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name_ru, name_by, description_ru, description_by, price, category_ru, category_by, attributes_ru, attributes_by, photo_id))
        connection.commit()
        logger.info(f"Товар добавлен: {name_ru}")
        return True
    except Exception as error:
        logger.error(f"Ошибка добавления товара: {error}")
        return False
    finally:
        connection.close()

def delete_product_from_database(product_id):
    try:
        connection = get_database_connection()
        connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
        connection.commit()
        logger.info(f"Товар удален: {product_id}")
    except Exception as error:
        logger.error(f"Ошибка удаления товара: {error}")
    finally:
        connection.close()

def toggle_product_stock_in_database(product_id):
    try:
        connection = get_database_connection()
        connection.execute("UPDATE products SET in_stock = NOT in_stock WHERE id = ?", (product_id,))
        connection.commit()
    except Exception as error:
        logger.error(f"Ошибка переключения стока: {error}")
    finally:
        connection.close()

def get_products_by_category_from_database(category_ru):
    try:
        connection = get_database_connection()
        products = connection.execute("SELECT * FROM products WHERE category_ru = ? ORDER BY name_ru", (category_ru,)).fetchall()
        return products
    except Exception as error:
        logger.error(f"Ошибка получения товаров категории: {error}")
        return []
    finally:
        connection.close()

def search_products_in_database(query):
    try:
        connection = get_database_connection()
        search_query = f'%{query}%'
        products = connection.execute("""
            SELECT * FROM products 
            WHERE name_ru LIKE ? OR name_by LIKE ? 
            OR description_ru LIKE ? OR description_by LIKE ? 
            OR attributes_ru LIKE ? OR attributes_by LIKE ?
        """, (search_query, search_query, search_query, search_query, search_query, search_query)).fetchall()
        return products
    except Exception as error:
        logger.error(f"Ошибка поиска: {error}")
        return []
    finally:
        connection.close()

def get_product_by_id_from_database(product_id):
    try:
        connection = get_database_connection()
        product = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return product
    except Exception as error:
        logger.error(f"Ошибка получения товара: {error}")
        return None
    finally:
        connection.close()

def get_all_products_from_database():
    try:
        connection = get_database_connection()
        products = connection.execute("SELECT * FROM products ORDER BY category_ru, name_ru").fetchall()
        return products
    except Exception as error:
        logger.error(f"Ошибка получения всех товаров: {error}")
        return []
    finally:
        connection.close()

def add_promotion_to_database(text_ru, text_by):
    try:
        connection = get_database_connection()
        connection.execute("INSERT INTO promotions (text_ru, text_by) VALUES (?, ?)", (text_ru, text_by))
        connection.commit()
        return True
    except Exception as error:
        logger.error(f"Ошибка добавления акции: {error}")
        return False
    finally:
        connection.close()

def delete_promotion_from_database(promotion_id):
    try:
        connection = get_database_connection()
        connection.execute("DELETE FROM promotions WHERE id = ?", (promotion_id,))
        connection.commit()
    except Exception as error:
        logger.error(f"Ошибка удаления акции: {error}")
    finally:
        connection.close()

def get_active_promotions_from_database():
    try:
        connection = get_database_connection()
        promotions = connection.execute("SELECT * FROM promotions WHERE active = 1").fetchall()
        return promotions
    except Exception as error:
        logger.error(f"Ошибка получения акций: {error}")
        return []
    finally:
        connection.close()

def get_all_promotions_from_database():
    try:
        connection = get_database_connection()
        promotions = connection.execute("SELECT * FROM promotions").fetchall()
        return promotions
    except Exception as error:
        logger.error(f"Ошибка получения всех акций: {error}")
        return []
    finally:
        connection.close()

def get_user_language_from_database(user_id):
    try:
        connection = get_database_connection()
        row = connection.execute("SELECT language FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row['language'] if row else 'ru'
    except Exception as error:
        logger.error(f"Ошибка получения языка: {error}")
        return 'ru'
    finally:
        connection.close()

def set_user_language_in_database(user_id, language):
    try:
        connection = get_database_connection()
        connection.execute("INSERT OR REPLACE INTO users (user_id, language) VALUES (?, ?)", (user_id, language))
        connection.commit()
    except Exception as error:
        logger.error(f"Ошибка установки языка: {error}")
    finally:
        connection.close()

def add_user_to_database(user_id):
    try:
        connection = get_database_connection()
        connection.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        connection.commit()
    except Exception as error:
        logger.error(f"Ошибка добавления пользователя: {error}")
    finally:
        connection.close()

def get_all_users_from_database():
    try:
        connection = get_database_connection()
        users = connection.execute("SELECT user_id FROM users").fetchall()
        return users
    except Exception as error:
        logger.error(f"Ошибка получения пользователей: {error}")
        return []
    finally:
        connection.close()

def get_users_count_from_database():
    try:
        connection = get_database_connection()
        count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        return count
    except Exception as error:
        logger.error(f"Ошибка подсчета пользователей: {error}")
        return 0
    finally:
        connection.close()

def get_products_count_from_database():
    try:
        connection = get_database_connection()
        count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        return count
    except Exception as error:
        logger.error(f"Ошибка подсчета товаров: {error}")
        return 0
    finally:
        connection.close()

# ==================== КОНСТАНТЫ ====================
CATEGORIES_RUSSIAN = ['Под-системы', 'Жидкости', 'Одноразки', 'Расходники', 'Снюсы']
CATEGORIES_BELARUSIAN = ['Пад-сістэмы', 'Вадкасці', 'Аднаразкі', 'Расходнікі', 'Снюсы']

CATEGORY_ATTRIBUTES_DICTIONARY = {
    'Под-системы': {'ru': 'цвета', 'by': 'колеры'},
    'Жидкости': {'ru': 'вкусы', 'by': 'смакі'},
    'Одноразки': {'ru': 'вкусы', 'by': 'смакі'},
    'Расходники': {'ru': 'тип', 'by': 'тып'},
    'Снюсы': {'ru': 'крепость', 'by': 'моцнасць'},
}

# ==================== ПРЕМИУМ ЭМОДЗИ ====================
PREMIUM_EMOJI = {
    "ghost": '<tg-emoji emoji-id="5116517977637782262">👻</tg-emoji>',
    "fire": '<tg-emoji emoji-id="5116414868357907335">🔥</tg-emoji>',
    "star": '<tg-emoji emoji-id="5116163917713769254">⭐️</tg-emoji>',
    "heart": '<tg-emoji emoji-id="5084974483685507801">💜</tg-emoji>',
    "check": '<tg-emoji emoji-id="5118861066981344121">✅</tg-emoji>',
    "cross": '<tg-emoji emoji-id="5116151848855667552">🚫</tg-emoji>',
    "money": '<tg-emoji emoji-id="5116648080787112958">💰</tg-emoji>',
    "shop": '<tg-emoji emoji-id="5118744200921219799">🎥</tg-emoji>',
    "user": '<tg-emoji emoji-id="5116582462276764538">👤</tg-emoji>',
    "lightning": '<tg-emoji emoji-id="5085022089103016925">⚡️</tg-emoji>',
    "package": '<tg-emoji emoji-id="5084979757905347540">✅</tg-emoji>',
    "skull": '<tg-emoji emoji-id="5125286720308249351">💀</tg-emoji>',
    "spider": '<tg-emoji emoji-id="5136449172806828766">🕷</tg-emoji>',
    "bomb": '<tg-emoji emoji-id="5134472688986756318">💣</tg-emoji>',
    "cool": '<tg-emoji emoji-id="5100657930429006538">♥️</tg-emoji>',
    "butterfly": '<tg-emoji emoji-id="5084613633418199991">🦋</tg-emoji>',
    "goat": '<tg-emoji emoji-id="5098094273039959279">🐐</tg-emoji>',
    "blue_heart": '<tg-emoji emoji-id="5082628525303792441">💙</tg-emoji>',
    "mute": '<tg-emoji emoji-id="5116466579764151159">🔇</tg-emoji>',
    "up": '<tg-emoji emoji-id="5116395218882528029">⏫</tg-emoji>',
}

# ==================== БОТ ====================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

user_states_dictionary = {}
age_verified_users_set = set()

# ==================== ОБЫЧНЫЕ КЛАВИАТУРЫ ====================
def get_main_keyboard(language='ru'):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if language == 'by':
        keyboard.add('Катэгорыі', 'Пошук')
        keyboard.add('Акцыі', 'Мэнэджар')
        keyboard.add('Змяніць мову')
    else:
        keyboard.add('Категории', 'Поиск')
        keyboard.add('Акции', 'Менеджер')
        keyboard.add('Сменить язык')
    return keyboard

def get_admin_main_keyboard(language='ru'):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if language == 'by':
        keyboard.add('Катэгорыі', 'Пошук')
        keyboard.add('Акцыі', 'Мэнэджар')
        keyboard.add('Змяніць мову', 'Адмін-панэль')
    else:
        keyboard.add('Категории', 'Поиск')
        keyboard.add('Акции', 'Менеджер')
        keyboard.add('Сменить язык', 'Админ-панель')
    return keyboard

def get_age_confirmation_keyboard(language='ru'):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if language == 'by':
        keyboard.add('Мне ёсць 18 гадоў')
        keyboard.add('Мне няма 18 гадоў')
    else:
        keyboard.add('Мне есть 18 лет')
        keyboard.add('Мне нет 18 лет')
    return keyboard

# ==================== ИНЛАЙН КЛАВИАТУРЫ ====================
def get_categories_inline_keyboard(language='ru'):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    categories_display = CATEGORIES_BELARUSIAN if language == 'by' else CATEGORIES_RUSSIAN
    
    for index, category_name in enumerate(categories_display):
        callback_data = f"category_{CATEGORIES_RUSSIAN[index]}"
        keyboard.add(types.InlineKeyboardButton(category_name, callback_data=callback_data))
    
    close_text = "Закрыть" if language == 'ru' else "Зачыніць"
    keyboard.add(types.InlineKeyboardButton(close_text, callback_data="close"))
    return keyboard

def get_products_inline_keyboard(category_ru, language='ru'):
    products = get_products_by_category_from_database(category_ru)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for product in products:
        product_name = product['name_by'] if language == 'by' else product['name_ru']
        stock_status = "✅" if product['in_stock'] else "❌"
        button_text = f"{stock_status} {product_name} — {product['price']:.2f} BYN"
        keyboard.add(types.InlineKeyboardButton(button_text, callback_data=f"product_{product['id']}"))
    
    back_text = "Назад к категориям" if language == 'ru' else "Назад да катэгорый"
    close_text = "Закрыть" if language == 'ru' else "Зачыніць"
    keyboard.add(types.InlineKeyboardButton(back_text, callback_data="categories"))
    keyboard.add(types.InlineKeyboardButton(close_text, callback_data="close"))
    return keyboard

def get_product_detail_inline_keyboard(product_id, language='ru'):
    product = get_product_by_id_from_database(product_id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    if product:
        # Кнопка КУПИТЬ
        product_name = product['name_ru']
        message_text = f"Здравствуйте, хочу купить {product_name}"
        encoded_text = quote(message_text)
        manager_username = MANAGER_USERNAME.replace('@', '')
        purchase_url = f"https://t.me/{manager_username}?text={encoded_text}"
        
        buy_text = "💰 Купить" if language == 'ru' else "💰 Купіць"
        keyboard.add(types.InlineKeyboardButton(buy_text, url=purchase_url))
        
        # Кнопка с атрибутами (цвета/вкусы/крепость)
        attributes = product['attributes_by'] if language == 'by' else product['attributes_ru']
        if attributes and attributes != '-':
            category = product['category_ru']
            attribute_name = CATEGORY_ATTRIBUTES_DICTIONARY.get(category, {}).get(language, '')
            if attribute_name:
                keyboard.add(types.InlineKeyboardButton(
                    f"📋 {attribute_name.capitalize()}",
                    callback_data=f"attributes_{product_id}"
                ))
    
    back_text = "Назад к категориям" if language == 'ru' else "Назад да катэгорый"
    close_text = "Закрыть" if language == 'ru' else "Зачыніць"
    keyboard.add(types.InlineKeyboardButton(back_text, callback_data="categories"))
    keyboard.add(types.InlineKeyboardButton(close_text, callback_data="close"))
    return keyboard

def get_admin_panel_inline_keyboard(language='ru'):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    add_text = "➕ Добавить товар" if language == 'ru' else "➕ Дадаць тавар"
    list_text = "📋 Список товаров" if language == 'ru' else "📋 Спіс тавараў"
    promo_add_text = "🔥 Добавить акцию" if language == 'ru' else "🔥 Дадаць акцыю"
    promo_list_text = "📢 Список акций" if language == 'ru' else "📢 Спіс акцый"
    stats_text = "📊 Статистика" if language == 'ru' else "📊 Статыстыка"
    mail_text = "📨 Рассылка" if language == 'ru' else "📨 Рассылка"
    close_text = "Закрыть" if language == 'ru' else "Зачыніць"
    
    keyboard.add(
        types.InlineKeyboardButton(add_text, callback_data="admin_add_product"),
        types.InlineKeyboardButton(list_text, callback_data="admin_list_products")
    )
    keyboard.add(
        types.InlineKeyboardButton(promo_add_text, callback_data="admin_add_promotion"),
        types.InlineKeyboardButton(promo_list_text, callback_data="admin_list_promotions")
    )
    keyboard.add(
        types.InlineKeyboardButton(stats_text, callback_data="admin_statistics"),
        types.InlineKeyboardButton(mail_text, callback_data="admin_mailing")
    )
    keyboard.add(types.InlineKeyboardButton(close_text, callback_data="close"))
    return keyboard

def get_confirm_inline_keyboard(language='ru'):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    yes_text = "✅ Да" if language == 'ru' else "✅ Так"
    no_text = "❌ Нет" if language == 'ru' else "❌ Не"
    
    keyboard.add(
        types.InlineKeyboardButton(yes_text, callback_data="confirm_yes"),
        types.InlineKeyboardButton(no_text, callback_data="confirm_no")
    )
    return keyboard

def get_category_selection_inline_keyboard(language='ru'):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    categories_display = CATEGORIES_BELARUSIAN if language == 'by' else CATEGORIES_RUSSIAN
    
    for index, category_name in enumerate(categories_display):
        callback_data = f"select_category_{CATEGORIES_RUSSIAN[index]}"
        keyboard.add(types.InlineKeyboardButton(category_name, callback_data=callback_data))
    
    keyboard.add(types.InlineKeyboardButton("Назад", callback_data="admin_back"))
    return keyboard

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def check_user_age_verified(message):
    if message.from_user.id not in age_verified_users_set:
        language = get_user_language_from_database(message.from_user.id)
        text = "Сначала подтверди возраст: /start" if language == 'ru' else "Спачатку пацвердзі ўзрост: /start"
        bot.send_message(message.chat.id, text)
        return False
    return True

def show_main_menu_to_user(message, language='ru'):
    if message.from_user.id == ADMIN_ID:
        keyboard = get_admin_main_keyboard(language)
    else:
        keyboard = get_main_keyboard(language)
    
    text = f"{PREMIUM_EMOJI['ghost']} <b>ВЕЙП-ШОП</b>\n\n{PREMIUM_EMOJI['heart']} Добро пожаловать!\n{PREMIUM_EMOJI['fire']} Лучшие девайсы в Беларуси"
    if language == 'by':
        text = f"{PREMIUM_EMOJI['ghost']} <b>ВЕЙП-ШОП</b>\n\n{PREMIUM_EMOJI['heart']} Вітаем!\n{PREMIUM_EMOJI['fire']} Лепшыя дэвайсы ў Беларусі"
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

def cancel_user_state(user_id):
    if user_id in user_states_dictionary:
        del user_states_dictionary[user_id]

# ==================== ХЕНДЛЕРЫ КОМАНД ====================
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    initialize_database()
    add_user_to_database(message.from_user.id)
    language = get_user_language_from_database(message.from_user.id)
    
    if message.from_user.id not in age_verified_users_set:
        text = f"{PREMIUM_EMOJI['ghost']} <b>ВЕЙП-ШОП 18+</b>\n\n{PREMIUM_EMOJI['fire']} Подтверди свой возраст:"
        if language == 'by':
            text = f"{PREMIUM_EMOJI['ghost']} <b>ВЕЙП-ШОП 18+</b>\n\n{PREMIUM_EMOJI['fire']} Пацвердзі свой узрост:"
        bot.send_message(message.chat.id, text, reply_markup=get_age_confirmation_keyboard(language))
    else:
        show_main_menu_to_user(message, language)

@bot.message_handler(commands=['admin'])
def handle_admin_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    language = get_user_language_from_database(message.from_user.id)
    text = f"{PREMIUM_EMOJI['lightning']} <b>АДМИН-ПАНЕЛЬ</b>"
    bot.send_message(message.chat.id, text, reply_markup=get_admin_panel_inline_keyboard(language))

@bot.message_handler(commands=['cancel'])
def handle_cancel_command(message):
    cancel_user_state(message.from_user.id)
    language = get_user_language_from_database(message.from_user.id)
    text = "❌ Действие отменено" if language == 'ru' else "❌ Дзеянне адменена"
    bot.send_message(message.chat.id, text)

# ==================== ПОДТВЕРЖДЕНИЕ ВОЗРАСТА ====================
@bot.message_handler(func=lambda message: message.text in ['Мне есть 18 лет', 'Мне нет 18 лет', 'Мне ёсць 18 гадоў', 'Мне няма 18 гадоў'])
def handle_age_confirmation(message):
    language = get_user_language_from_database(message.from_user.id)
    
    if message.text in ['Мне есть 18 лет', 'Мне ёсць 18 гадоў']:
        age_verified_users_set.add(message.from_user.id)
        text = f"{PREMIUM_EMOJI['check']} Доступ разрешён!" if language == 'ru' else f"{PREMIUM_EMOJI['check']} Доступ дазволены!"
        bot.send_message(message.chat.id, text)
        show_main_menu_to_user(message, language)
    else:
        text = f"{PREMIUM_EMOJI['cross']} Доступ запрещён!" if language == 'ru' else f"{PREMIUM_EMOJI['cross']} Доступ забаронены!"
        bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())

# ==================== ОСНОВНЫЕ КНОПКИ МЕНЮ ====================
@bot.message_handler(func=lambda message: message.text in ['Сменить язык', 'Змяніць мову'])
def handle_change_language_button(message):
    if not check_user_age_verified(message):
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton('🇷🇺 Русский', callback_data='set_language_ru'),
        types.InlineKeyboardButton('🇧🇾 Беларуская', callback_data='set_language_by')
    )
    bot.send_message(message.chat.id, '<b>Выбери язык / Выберы мову:</b>', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in ['Категории', 'Катэгорыі'])
def handle_categories_button(message):
    if not check_user_age_verified(message):
        return
    
    language = get_user_language_from_database(message.from_user.id)
    text = f"{PREMIUM_EMOJI['shop']} <b>КАТЕГОРИИ</b>" if language == 'ru' else f"{PREMIUM_EMOJI['shop']} <b>КАТЭГОРЫІ</b>"
    bot.send_message(message.chat.id, text, reply_markup=get_categories_inline_keyboard(language))

@bot.message_handler(func=lambda message: message.text in ['Поиск', 'Пошук'])
def handle_search_button(message):
    if not check_user_age_verified(message):
        return
    
    language = get_user_language_from_database(message.from_user.id)
    user_states_dictionary[message.from_user.id] = {"action": "search"}
    
    text = f"{PREMIUM_EMOJI['star']} <b>ПОИСК</b>\n\nВведи название товара:" if language == 'ru' else f"{PREMIUM_EMOJI['star']} <b>ПОШУК</b>\n\nУвядзі назву тавару:"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text in ['Акции', 'Акцыі'])
def handle_promotions_button(message):
    if not check_user_age_verified(message):
        return
    
    language = get_user_language_from_database(message.from_user.id)
    promotions = get_active_promotions_from_database()
    
    if promotions:
        text = f"{PREMIUM_EMOJI['fire']} <b>АКЦИИ</b>\n\n" if language == 'ru' else f"{PREMIUM_EMOJI['fire']} <b>АКЦЫІ</b>\n\n"
        for promotion in promotions:
            promotion_text = promotion['text_by'] if language == 'by' else promotion['text_ru']
            text += f"{PREMIUM_EMOJI['star']} {promotion_text}\n\n"
    else:
        text = f"{PREMIUM_EMOJI['cross']} Нет акций" if language == 'ru' else f"{PREMIUM_EMOJI['cross']} Няма акцый"
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text in ['Менеджер', 'Мэнэджар'])
def handle_manager_button(message):
    if not check_user_age_verified(message):
        return
    
    language = get_user_language_from_database(message.from_user.id)
    text = f"{PREMIUM_EMOJI['ghost']} <b>МЕНЕДЖЕР</b>\n\n{PREMIUM_EMOJI['heart']} Связь:\n{PREMIUM_EMOJI['user']} {MANAGER_USERNAME}"
    if language == 'by':
        text = f"{PREMIUM_EMOJI['ghost']} <b>МЭНЭДЖАР</b>\n\n{PREMIUM_EMOJI['heart']} Сувязь:\n{PREMIUM_EMOJI['user']} {MANAGER_USERNAME}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text in ['Главная', 'Галоўная'])
def handle_home_button(message):
    if not check_user_age_verified(message):
        return
    
    language = get_user_language_from_database(message.from_user.id)
    show_main_menu_to_user(message, language)

@bot.message_handler(func=lambda message: message.text in ['Админ-панель', 'Адмін-панэль'])
def handle_admin_panel_button(message):
    if not check_user_age_verified(message):
        return
    
    if message.from_user.id != ADMIN_ID:
        return
    
    language = get_user_language_from_database(message.from_user.id)
    text = f"{PREMIUM_EMOJI['lightning']} <b>АДМИН-ПАНЕЛЬ</b>"
    bot.send_message(message.chat.id, text, reply_markup=get_admin_panel_inline_keyboard(language))

# ==================== ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ====================
@bot.message_handler(func=lambda message: True)
def handle_all_text_messages(message):
    user_id = message.from_user.id
    
    if user_id not in age_verified_users_set:
        return
    
    language = get_user_language_from_database(user_id)
    
    # Обработка поиска
    if user_id in user_states_dictionary and user_states_dictionary[user_id].get("action") == "search":
        products = search_products_in_database(message.text)
        cancel_user_state(user_id)
        
        if products:
            text = f"{PREMIUM_EMOJI['star']} <b>Результаты поиска:</b>\n\n"
            for product in products[:10]:
                product_name = product['name_by'] if language == 'by' else product['name_ru']
                text += f"<b>{product_name}</b> — {product['price']:.2f} BYN\n"
        else:
            text = f"{PREMIUM_EMOJI['cross']} Ничего не найдено"
        
        bot.send_message(message.chat.id, text)
        return
    
    # Обработка рассылки
    if user_id in user_states_dictionary and user_states_dictionary[user_id].get("action") == "mailing":
        mailing_text = message.text
        users = get_all_users_from_database()
        success_count = 0
        
        for user in users:
            try:
                bot.send_message(user['user_id'], mailing_text)
                success_count += 1
            except:
                pass
        
        cancel_user_state(user_id)
        bot.send_message(message.chat.id, f"✅ Рассылка отправлена! Доставлено: {success_count} пользователей.")
        return
    
    # Обработка состояний админа
    if user_id == ADMIN_ID and user_id in user_states_dictionary:
        state = user_states_dictionary[user_id]
        handle_admin_state_machine(message, state, language)
        return

# ==================== МАШИНА СОСТОЯНИЙ АДМИНА ====================
def handle_admin_state_machine(message, state, language):
    user_id = message.from_user.id
    
    # Добавление акции
    if state.get("action") == "add_promotion":
        if state["step"] == "text":
            text_ru = message.text.strip()
            text_by = translate_to_belarusian(text_ru)
            state["text_ru"] = text_ru
            state["text_by"] = text_by
            state["step"] = "confirm"
            
            confirm_text = f"{PREMIUM_EMOJI['fire']} <b>АКЦИЯ:</b>\n\nRU: {text_ru}\nBY: {text_by}\n\nДобавить?"
            bot.send_message(message.chat.id, confirm_text, reply_markup=get_confirm_inline_keyboard(language))
        return
    
    # Добавление товара
    if state.get("action") == "add_product":
        step = state["step"]
        data = state.get("data", {})
        
        if step == "name":
            data['name_ru'] = message.text.strip()
            data['name_by'] = translate_to_belarusian(data['name_ru'])
            state["step"] = "price"
            state["data"] = data
            
            text = "Введи <b>цену</b> (число, например 49.90):" if language == 'ru' else "Увядзі <b>кошт</b> (лік, напрыклад 49.90):"
            bot.send_message(message.chat.id, text, reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("Назад", callback_data="admin_back")
            ))
        
        elif step == "price":
            try:
                price = float(message.text.strip().replace(',', '.'))
                if price <= 0:
                    raise ValueError
                data['price'] = price
                state["step"] = "description"
                state["data"] = data
                
                text = "Введи <b>описание</b> (или \"-\" пропустить):" if language == 'ru' else "Увядзі <b>апісанне</b> (або \"-\" прапусціць):"
                bot.send_message(message.chat.id, text)
            except:
                text = "❌ Ошибка! Введи корректное число!" if language == 'ru' else "❌ Памылка! Увядзі карэктны лік!"
                bot.send_message(message.chat.id, text)
        
        elif step == "description":
            if message.text.strip() == '-':
                data['description_ru'] = ''
                data['description_by'] = ''
            else:
                data['description_ru'] = message.text.strip()
                data['description_by'] = translate_to_belarusian(data['description_ru'])
            
            state["step"] = "photo"
            state["data"] = data
            
            text = "📸 Отправь <b>фото товара</b> (или \"-\" пропустить):" if language == 'ru' else "📸 Дашлі <b>фота тавару</b> (або \"-\" прапусціць):"
            bot.send_message(message.chat.id, text)
        
        elif step == "photo":
            state["step"] = "category"
            
            text = "<b>📁 Выбери категорию:</b>" if language == 'ru' else "<b>📁 Выберы катэгорыю:</b>"
            bot.send_message(message.chat.id, text, reply_markup=get_category_selection_inline_keyboard(language))
        
        elif step == "attributes":
            if message.text.strip() == '-':
                data['attributes_ru'] = ''
                data['attributes_by'] = ''
            else:
                data['attributes_ru'] = message.text.strip()
                data['attributes_by'] = translate_to_belarusian(data['attributes_ru'])
            
            state["step"] = "confirm"
            state["data"] = data
            
            category = data.get('category_ru', '')
            attribute_name = CATEGORY_ATTRIBUTES_DICTIONARY.get(category, {}).get(language, '')
            
            confirm_text = f"{PREMIUM_EMOJI['check']} <b>ПРОВЕРКА:</b>\n\n"
            confirm_text += f"Название: {data['name_ru']}\n"
            confirm_text += f"Цена: {data['price']} BYN\n"
            confirm_text += f"Категория: {data['category_ru']}\n"
            confirm_text += f"Описание: {data.get('description_ru', '-') or '-'}\n"
            confirm_text += f"{attribute_name.capitalize()}: {data.get('attributes_ru', '-') or '-'}\n"
            confirm_text += f"Фото: {'✅' if data.get('photo_id') else '❌'}\n\n"
            confirm_text += "Всё верно?" if language == 'ru' else "Усё дакладна?"
            
            bot.send_message(message.chat.id, confirm_text, reply_markup=get_confirm_inline_keyboard(language))
        return

# ==================== ОБРАБОТЧИК ФОТОГРАФИЙ ====================
@bot.message_handler(content_types=['photo'])
def handle_photo_message(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    if user_id not in user_states_dictionary:
        return
    
    state = user_states_dictionary[user_id]
    
    if state.get("action") == "add_product" and state.get("step") == "photo":
        state["data"]["photo_id"] = message.photo[-1].file_id
        language = get_user_language_from_database(user_id)
        state["step"] = "category"
        
        text = "✅ Фото сохранено!\n\n<b>📁 Выбери категорию:</b>" if language == 'ru' else "✅ Фота захавана!\n\n<b>📁 Выберы катэгорыю:</b>"
        bot.send_message(message.chat.id, text, reply_markup=get_category_selection_inline_keyboard(language))

# ==================== ОБРАБОТЧИК CALLBACK ЗАПРОСОВ ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callback_queries(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    callback_data = call.data
    language = get_user_language_from_database(call.from_user.id)
    
    try:
        # Закрыть
        if callback_data == 'close':
            bot.delete_message(chat_id, message_id)
            return
        
        # Языки
        if callback_data.startswith('set_language_'):
            new_lang = callback_data.split('_')[2]
            set_user_language_in_database(call.from_user.id, new_lang)
            bot.answer_callback_query(call.id, '✅ Язык изменён!' if new_lang == 'ru' else '✅ Мова зменена!')
            bot.delete_message(chat_id, message_id)
            show_main_menu_to_user(call.message, new_lang)
            return
        
        # Категории
        if callback_data == 'categories':
            text = f"{PREMIUM_EMOJI['shop']} <b>КАТЕГОРИИ</b>" if language == 'ru' else f"{PREMIUM_EMOJI['shop']} <b>КАТЭГОРЫІ</b>"
            try:
                bot.edit_message_text(text, chat_id, message_id, reply_markup=get_categories_inline_keyboard(language))
            except:
                bot.send_message(chat_id, text, reply_markup=get_categories_inline_keyboard(language))
            return
        
        # Товары категории
        if callback_data.startswith('category_'):
            category_ru = callback_data.replace('category_', '')
            text = f"{PREMIUM_EMOJI['shop']} <b>{category_ru}</b>"
            try:
                bot.edit_message_text(text, chat_id, message_id, reply_markup=get_products_inline_keyboard(category_ru, language))
            except:
                bot.send_message(chat_id, text, reply_markup=get_products_inline_keyboard(category_ru, language))
            return
        
        # Карточка товара
        if callback_data.startswith('product_'):
            pid = int(callback_data.split('_')[1])
            p = get_product_by_id_from_database(pid)
            if p:
                text = format_product_card(p, language)
                if p['photo_id']:
                    bot.delete_message(chat_id, message_id)
                    bot.send_photo(chat_id, p['photo_id'], caption=text, reply_markup=get_product_detail_inline_keyboard(pid, language))
                else:
                    try:
                        bot.edit_message_text(text, chat_id, message_id, reply_markup=get_product_detail_inline_keyboard(pid, language))
                    except:
                        bot.send_message(chat_id, text, reply_markup=get_product_detail_inline_keyboard(pid, language))
            return
        
        # Атрибуты
        if callback_data.startswith('attributes_'):
            pid = int(callback_data.split('_')[1])
            p = get_product_by_id_from_database(pid)
            if p:
                attr = p['attributes_by'] if language == 'by' else p['attributes_ru']
                name = p['name_by'] if language == 'by' else p['name_ru']
                cat = p['category_ru']
                attr_name = CATEGORY_ATTRIBUTES_DICTIONARY.get(cat, {}).get(language, '')
                
                if attr and attr != '-':
                    items = [x.strip() for x in attr.split(',')]
                    text = f"{PREMIUM_EMOJI['ghost']} <b>{name}</b>\n\n📋 <b>{attr_name.capitalize()}:</b>\n\n"
                    for item in items:
                        text += f"• {item}\n"
                else:
                    text = f"Нет информации о {attr_name}"
                
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton('Назад', callback_data=f"product_{pid}"))
                bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
            return
        
        # АДМИНКА
        if callback_data == 'admin_back':
            bot.edit_message_text(
                f"{PREMIUM_EMOJI['lightning']} <b>АДМИН-ПАНЕЛЬ</b>",
                chat_id, message_id,
                reply_markup=get_admin_panel_inline_keyboard(language))
            return
        
        if callback_data == 'admin_statistics':
            users = get_users_count_from_database()
            products = get_products_count_from_database()
            text = f"{PREMIUM_EMOJI['star']} <b>СТАТИСТИКА:</b>\n\n{PREMIUM_EMOJI['user']} Пользователей: {users}\n{PREMIUM_EMOJI['shop']} Товаров: {products}"
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Назад', callback_data='admin_back'))
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
            return
        
        if callback_data == 'admin_mailing':
            user_states_dictionary[call.from_user.id] = {"action": "mailing"}
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Назад', callback_data='admin_back'))
            bot.edit_message_text('📨 Введи текст рассылки:', chat_id, message_id, reply_markup=kb)
            return
        
        if callback_data == 'admin_list_products':
            products = get_all_products_from_database()
            text = f"{PREMIUM_EMOJI['fire']} <b>ВСЕ ТОВАРЫ:</b>\n\n"
            for p in products:
                s = '✅' if p['in_stock'] else '❌'
                text += f"{s} {p['name_ru']} — {p['price']:.2f} BYN | {p['category_ru']}\n"
            if not products:
                text = 'Товаров нет'
            
            kb = types.InlineKeyboardMarkup(row_width=3)
            for p in products:
                kb.add(
                    types.InlineKeyboardButton(p['name_ru'][:15], callback_data=f"admin_info_{p['id']}"),
                    types.InlineKeyboardButton('✅' if p['in_stock'] else '❌', callback_data=f"admin_toggle_{p['id']}"),
                    types.InlineKeyboardButton('🗑', callback_data=f"admin_delete_{p['id']}")
                )
            kb.add(types.InlineKeyboardButton('Назад', callback_data='admin_back'))
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
            return
        
        if callback_data.startswith('admin_delete_'):
            pid = int(callback_data.split('_')[2])
            delete_product_from_database(pid)
            bot.answer_callback_query(call.id, '✅ Удалено!')
            call.data = 'admin_list_products'
            handle_all_callback_queries(call)
            return
        
        if callback_data.startswith('admin_toggle_'):
            pid = int(callback_data.split('_')[2])
            toggle_product_stock_in_database(pid)
            bot.answer_callback_query(call.id, '✅ Статус изменён!')
            call.data = 'admin_list_products'
            handle_all_callback_queries(call)
            return
        
        if callback_data == 'admin_add_product':
            user_states_dictionary[call.from_user.id] = {"action": "add_product", "step": "name", "data": {}}
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Назад', callback_data='admin_back'))
            bot.edit_message_text('Введи <b>название товара</b> (на русском):', chat_id, message_id, reply_markup=kb)
            return
        
        if callback_data == 'admin_add_promotion':
            user_states_dictionary[call.from_user.id] = {"action": "add_promotion", "step": "text"}
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Назад', callback_data='admin_back'))
            bot.edit_message_text('Введи <b>текст акции</b> (на русском):', chat_id, message_id, reply_markup=kb)
            return
        
        if callback_data == 'admin_list_promotions':
            promos = get_all_promotions_from_database()
            text = f"{PREMIUM_EMOJI['fire']} <b>АКЦИИ:</b>\n\n"
            for p in promos:
                text += f"RU: {p['text_ru']}\nBY: {p['text_by']}\n\n"
            if not promos:
                text = 'Акций нет'
            
            kb = types.InlineKeyboardMarkup(row_width=1)
            for p in promos:
                kb.add(types.InlineKeyboardButton(f"🗑 {p['text_ru'][:40]}", callback_data=f"promotion_delete_{p['id']}"))
            kb.add(types.InlineKeyboardButton('Назад', callback_data='admin_back'))
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
            return
        
        if callback_data.startswith('promotion_delete_'):
            pid = int(callback_data.split('_')[2])
            delete_promotion_from_database(pid)
            bot.answer_callback_query(call.id, '✅ Удалено!')
            call.data = 'admin_list_promotions'
            handle_all_callback_queries(call)
            return
        
        if callback_data.startswith('select_category_'):
            cr = callback_data.replace('select_category_', '')
            if call.from_user.id not in user_states_dictionary:
                bot.answer_callback_query(call.id, '❌ Ошибка!')
                return
            
            idx = CATEGORIES_RUSSIAN.index(cr)
            cb = CATEGORIES_BELARUSIAN[idx]
            user_states_dictionary[call.from_user.id]['data']['category_ru'] = cr
            user_states_dictionary[call.from_user.id]['data']['category_by'] = cb
            user_states_dictionary[call.from_user.id]['step'] = 'attributes'
            
            attr_ru = CATEGORY_ATTRIBUTES_DICTIONARY.get(cr, {}).get('ru', '')
            kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Назад', callback_data='admin_back'))
            bot.edit_message_text(f'Введи <b>{attr_ru}</b> через запятую (или "-"):', chat_id, message_id, reply_markup=kb)
            return
        
        # Подтверждение ДА
        if callback_data == 'confirm_yes':
            uid = call.from_user.id
            if uid in user_states_dictionary:
                state = user_states_dictionary[uid]
                
                if state.get("action") == "add_product" and state.get("step") == "confirm":
                    d = state["data"]
                    ok = add_product_to_database(d['name_ru'], d['name_by'], d['price'], d['category_ru'], d['category_by'],
                        d.get('description_ru',''), d.get('description_by',''),
                        d.get('attributes_ru',''), d.get('attributes_by',''),
                        d.get('photo_id',''))
                    cancel_user_state(uid)
                    bot.answer_callback_query(call.id, '✅ Товар добавлен!' if ok else '❌ Ошибка!')
                    bot.send_message(chat_id, f"{PREMIUM_EMOJI['check']} <b>ТОВАР ДОБАВЛЕН!</b>" if ok else "❌ Ошибка")
                    bot.send_message(chat_id, f"{PREMIUM_EMOJI['lightning']} <b>АДМИН-ПАНЕЛЬ</b>", reply_markup=get_admin_panel_inline_keyboard(language))
                    return
                
                if state.get("action") == "add_promotion" and state.get("step") == "confirm":
                    ok = add_promotion_to_database(state['text_ru'], state['text_by'])
                    cancel_user_state(uid)
                    bot.answer_callback_query(call.id, '✅ Акция добавлена!' if ok else '❌ Ошибка!')
                    bot.send_message(chat_id, f"{PREMIUM_EMOJI['check']} <b>АКЦИЯ ДОБАВЛЕНА!</b>" if ok else "❌ Ошибка")
                    bot.send_message(chat_id, f"{PREMIUM_EMOJI['lightning']} <b>АДМИН-ПАНЕЛЬ</b>", reply_markup=get_admin_panel_inline_keyboard(language))
                    return
            return
        
        # Подтверждение НЕТ
        if callback_data == 'confirm_no':
            cancel_user_state(call.from_user.id)
            bot.answer_callback_query(call.id, '❌ Отменено')
            bot.send_message(chat_id, f"{PREMIUM_EMOJI['lightning']} <b>АДМИН-ПАНЕЛЬ</b>", reply_markup=get_admin_panel_inline_keyboard(language))
            return
    
    except Exception as error:
        logger.error(f"Callback error: {error}")
        try:
            bot.answer_callback_query(call.id, '❌ Ошибка')
        except:
            pass

def format_product_card(p, lang):
    name = p['name_by'] if lang == 'by' else p['name_ru']
    desc = p['description_by'] if lang == 'by' else p['description_ru']
    attr = p['attributes_by'] if lang == 'by' else p['attributes_ru']
    stock = f"{PREMIUM_EMOJI['check']} В наличии" if p['in_stock'] else f"{PREMIUM_EMOJI['cross']} Нет"
    cat = p['category_ru']
    attr_name = CATEGORY_ATTRIBUTES_DICTIONARY.get(cat, {}).get(lang, '')
    
    text = f"{PREMIUM_EMOJI['ghost']} <b>{name}</b>\n\n"
    if desc and desc != '-':
        text += f"📝 <b>Описание:</b> {desc}\n\n"
    text += f"{PREMIUM_EMOJI['money']} <b>Цена:</b> {p['price']:.2f} BYN\n"
    text += f"📦 <b>Статус:</b> {stock}\n"
    if attr and attr != '-' and attr_name:
        text += f"📋 <b>{attr_name.capitalize()}:</b> {attr}\n"
    return text

# ==================== ЗАПУСК БОТА ====================
if __name__ == '__main__':
    print("✅ Бот запущен!")
    initialize_database()
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as error:
            logger.error(f"Критическая ошибка polling: {error}")
            time.sleep(5)
