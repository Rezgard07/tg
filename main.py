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

# Данные бота
TOKEN = "8354164344:AAGfLAdD6_tRY6wFc5_2gerCTZ9HIy-wBjU"
OWNER = "@rezgard" # Твой юзернейм в телеге

bot = Bot(token=TOKEN)
dp = Dispatcher()
speller = YandexSpeller()

# Инициализация БД
def init_db():
    conn = sqlite3.connect('stats.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0)')
    conn.commit()
    conn.close()

# Клавиатура
def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Моя статистика")
    builder.button(text="🆘 Помощь / О боте")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Веб-сервер для Render
async def handle(request): return web.Response(text="Bot is Live")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    init_db()
    await message.answer(
        f"👋 <b>Дарова! Ты в главном меню.</b>\n\n"
        f"Я исправляю ошибки и перевожу текст автоматически.\n"
        f"Просто напиши мне что-нибудь!",
        parse_mode="HTML",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "🆘 Помощь / О боте")
async def show_help(message: types.Message):
    help_text = (
        f"🚀 <b>Функции бота:</b>\n"
        f"1. <b>Авто-исправление:</b> проверяю ошибки в RU тексте.\n"
        f"2. <b>Переводчик:</b> RU ↔ EN определяется сам.\n"
        f"3. <b>Статистика:</b> считаю твои успехи.\n\n"
        f"👨‍💻 <b>Создатель:</b> {OWNER}\n"
        f"<i>Сделано специально для удобного обучения!</i>"
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.message(F.text == "📊 Моя статистика")
async def show_stats(message: types.Message):
    conn = sqlite3.connect('stats.db')
    res = conn.execute('SELECT count FROM users WHERE id = ?', (message.from_user.id,)).fetchone()
    count = res[0] if res else 0
    conn.close()
    await message.answer(f"📈 Ты успешно обработал сообщений: <b>{count}</b>", parse_mode="HTML")

@dp.message()
async def handle_message(message: types.Message):
    if not message.text or message.text.startswith("/"): return
    
    # Обновление статистики
    conn = sqlite3.connect('stats.db')
    conn.execute('INSERT OR IGNORE INTO users (id, count) VALUES (?, 0)', (message.from_user.id,))
    conn.execute('UPDATE users SET count = count + 1 WHERE id = ?', (message.from_user.id,))
    conn.commit()
    conn.close()

    text = message.text
    try:
        # Проверка орфографии
        corrected = speller.spelled(text)
        is_rus = any(c in "абвгдейёжзийклмнопрстуфхцчшщъыьэюя" for c in text.lower())
        
        # Перевод
        target_lang = 'en' if is_rus else 'ru'
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        
        # Умная справка
        if len(text.split()) == 1:
            info = "💡 <b>Совет:</b> используйте это слово в контексте предложения для более точного перевода."
        else:
            info = f"💡 <b>Факт:</b> перевод выполнен на {'английский' if is_rus else 'русский'} язык."

        response = (
            f"🔍 <b>Статус:</b> {'✅ Ошибок нет' if text == corrected else '❌ Исправлено'}\n"
            f"📝 <b>Правка:</b> <code>{corrected}</code>\n"
            f"🌐 <b>Перевод:</b> <code>{translated}</code>\n\n"
            f"{info}"
        )
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Error: {e}")

async def main():
    init_db()
    # Запуск веб-сервера
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
