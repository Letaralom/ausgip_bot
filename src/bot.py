import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get('8342641332:AAGhf3sYgJTKuhkMo0bZV4IfOxKRVctXobc')
ADMIN_IDS = [int(id.strip()) for id in os.environ.get('ADMIN_IDS', '1189229455').split(',') if id.strip()]

# Автоматические пути для Railway
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, "works_database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "works_storage")

# Создаем папки если нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== БАЗА ДАННЫХ =====
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                parent_id INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Основные категории
        main_categories = ['ТЕХ_МЕХ', 'ЭЛ_ТЕХ', 'ГЕОД', 'ПСК', 'АРХ', 'ТОСП']
        for category in main_categories:
            cursor.execute("INSERT OR IGNORE INTO categories (name, parent_id) VALUES (?, NULL)", (category,))
        
        conn.commit()
        conn.close()
        logger.info("✅ База данных готова!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка базы данных: {e}")

# ===== КОМАНДА /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        logger.info(f"Пользователь {user_id} запустил бота")
        
        # Создаем кнопки
        keyboard = [
            [InlineKeyboardButton("📁 ТЕХ_МЕХ", callback_data="cat_1")],
            [InlineKeyboardButton("📁 ЭЛ_ТЕХ", callback_data="cat_2")],
            [InlineKeyboardButton("📁 ГЕОД", callback_data="cat_3")],
            [InlineKeyboardButton("📁 ПСК", callback_data="cat_4")],
            [InlineKeyboardButton("📁 АРХ", callback_data="cat_5")],
            [InlineKeyboardButton("📁 ТОСП", callback_data="cat_6")],
        ]
        
        # Если админ - добавляем кнопки управления
        if user_id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("➕ Добавить работу", callback_data="admin_add")])
            logger.info(f"Админ {user_id} вошел в систему")
    
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🎓 Выберите предмет:", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")

# ===== ОБРАБОТЧИК КНОПОК =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Нажата кнопка: {data}")
        
        if data.startswith("cat_"):
            category_id = int(data[4:])
            await show_files(query, category_id)
            
        elif data == "back_main":
            await start_from_callback(query)
            
    except Exception as e:
        logger.error(f"Ошибка в button_handler: {e}")

async def show_files(query, category_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Получаем название категории
        cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        result = cursor.fetchone()
        
        if not result:
            await query.edit_message_text("❌ Категория не найдена")
            return
            
        category_name = result[0]
        
        # Получаем файлы этой категории
        cursor.execute("SELECT id, filename FROM files WHERE category_id = ?", (category_id,))
        files = cursor.fetchall()
        
        # Создаем кнопки файлов
        keyboard = []
        for file_id, filename in files:
            keyboard.append([InlineKeyboardButton(f"📄 {filename}", callback_data=f"file_{file_id}")])
        
        # Кнопка назад
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_main")])
        
        conn.close()
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"📂 {category_name}\nВыберите работу:", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в show_files: {e}")

async def start_from_callback(query):
    try:
        user_id = query.from_user.id
        
        keyboard = [
            [InlineKeyboardButton("📁 ТЕХ_МЕХ", callback_data="cat_1")],
            [InlineKeyboardButton("📁 ЭЛ_ТЕХ", callback_data="cat_2")],
            [InlineKeyboardButton("📁 ГЕОД", callback_data="cat_3")],
            [InlineKeyboardButton("📁 ПСК", callback_data="cat_4")],
            [InlineKeyboardButton("📁 АРХ", callback_data="cat_5")],
            [InlineKeyboardButton("📁 ТОСП", callback_data="cat_6")],
        ]
        
        if user_id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("➕ Добавить работу", callback_data="admin_add")])
    
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🎓 Выберите предмет:", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в start_from_callback: {e}")

# ===== ЗАПУСК БОТА =====
def main():
    logger.info("🚀 Запускаю бота...")
    
    # Проверяем токен
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен! Проверь переменные окружения на Railway.")
        return
    
    # Инициализация БД
    init_db()
    
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Запускаем бота
        logger.info("✅ Бот запущен и готов к работе!")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()
