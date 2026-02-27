import logging
import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from deep_translator import GoogleTranslator
from aiohttp import web
from pyaspeller import YandexSpeller

# Настройки
TOKEN = "8354164344:AAGfLAdD6_tRY6wFc5_2gerCTZ9HIy-wBjU"
ADMIN_ID = 0  # Можешь вписать свой ID из Telegram, чтобы только ты видел статку
bot = Bot(token=TOKEN)
dp = Dispatcher()
speller = YandexSpeller()

# База данных для статистики
def init_db():
    conn = sqlite3.connect('stats.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0)')
    conn.commit()
    conn.close()

def update_stats(user_id):
    conn = sqlite3.connect('stats.db')
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (id, count) VALUES (?, 0)', (user_id,))
    cur.execute('UPDATE users SET count = count + 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

# Кнопки
def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Моя статистика")
    builder.button(text="🆘 Помощь")
    return builder.as_markup(resize_keyboard=True)

# Веб-сервер для Render
async def handle(request):
    return web.Response(text="Бот rezgard в порядке!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    init_db()
    await message.answer(
        f"👋 Дарова! Я бот-помощник от <b>rezgard</b>.\n\n"
        "Просто пришли текст — я исправлю ошибки и переведу.\n"
        "Используй кнопки ниже для управления!",
        parse_mode="HTML",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📊 Моя статистика")
async def show_stats(message: types.Message):
    conn = sqlite3.connect('stats.db')
    cur = conn.cursor()
    cur.execute('SELECT count FROM users WHERE id = ?', (message.from_user.id,))
    res = cur.fetchone()
    count = res[0] if res else 0
    await message.answer(f"👤 Ты обработал сообщений: <b>{count}</b>", parse_mode="HTML")

@dp.message()
async def handle_message(message: types.Message):
    if not message.text or message.text.startswith("/"): return
    
    update_stats(message.from_user.id)
    text = message.text
    
    try:
        # 1. Проверка ошибок
        corrected_text = speller.spelled(text)
        has_errors = "❌ Исправлены ошибки" if text != corrected_text else "✅ Ошибок нет"
        
        # 2. Перевод и Словари (Примеры)
        if any(c in "абвгдейёжзийклмнопрстуфхцчшщъыьэюя" for c in text.lower()):
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            direction = "🇷🇺 RU ➡️ 🇺🇸 EN"
            # Пример использования (простейший)
            example = "<i>Example: I love coding in Python.</i>"
        else:
            translated = GoogleTranslator(source='auto', target='ru').translate(text)
            direction = "🇺🇸 EN ➡️ 🇷🇺 RU"
            example = "<i>Пример: Мне нравится программировать.</i>"

        await message.answer(
            f"🔍 <b>Статус:</b> {has_errors}\n"
            f"📝 <b>Правка:</b> <code>{corrected_text}</code>\n\n"
            f"🌐 <b>{direction}:</b>\n<code>{translated}</code>\n\n"
            f"💡 <b>Для справки:</b>\n{example}",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Error: {e}")

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
