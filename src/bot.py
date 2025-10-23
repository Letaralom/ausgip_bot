import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get('BOT_TOKEN','YOUR_BOT_TOKEN_HERE')
ADMIN_IDS = [int(id.strip()) for id in os.environ.get('ADMIN_IDS', '123456789').split(',')]

# Автоматические пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, "works_database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "works_storage")

# Создаем папки если нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===== БАЗА ДАННЫХ =====
def init_db():
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
    print("✅ База данных готова!")

# ===== КОМАНДА /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
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
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎓 Выберите предмет:", reply_markup=reply_markup)

# ===== ОБРАБОТЧИК КНОПОК =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("cat_"):
        category_id = int(data[4:])
        await show_files(query, category_id)

async def show_files(query, category_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Получаем название категории
    cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
    category_name = cursor.fetchone()[0]
    
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

# ===== ЗАПУСК БОТА =====
def main():
    print("🚀 Запускаю бота...")
    
    # Инициализация БД
    init_db()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    print("✅ Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
