import logging
import asyncio
import os
import io
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

# --- НАСТРОЙКИ ---
TOKEN = "8354164344:AAGfLAdD6_tRY6wFc5_2gerCTZ9HIy-wBjU"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЛОГИКА АКЦИЙ ---
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")
    if hist.empty:
        return None
    
    current_price = hist['Close'].iloc[-1]
    change_1m = ((current_price - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) * 100 if len(hist) > 21 else 0
    change_1y = ((current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
    
    # Простейший прогноз (SMA)
    sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
    prob_up = 65 if current_price > sma_20 else 35
    prob_down = 100 - prob_up
    
    return {
        "price": round(current_price, 2),
        "1m": round(change_1m, 1),
        "1y": round(change_1y, 1),
        "up": prob_up,
        "down": prob_down,
        "hist": hist
    }

def create_chart(hist, ticker):
    plt.figure(figsize=(10, 5))
    plt.plot(hist.index, hist['Close'], color='blue', linewidth=2)
    plt.title(f"График {ticker} (1 год)")
    plt.grid(True)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# --- КОМАНДЫ БОТА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "📈 <b>Бот-инвестор готов!</b>\n\n"
        "Введи тикер акции (например: <code>AAPL</code> или <code>GAZP.ME</code>),\n"
        "чтобы получить цену, график и прогноз.",
        parse_mode="HTML"
    )

@dp.message()
async def handle_stock(message: types.Message):
    ticker = message.text.upper().strip()
    msg = await message.answer("🔄 Загружаю данные...")
    
    try:
        data = get_stock_data(ticker)
        if not data:
            return await msg.edit_text("❌ Тикер не найден. Попробуй AAPL или MSFT.")
        
        # Формируем текст
        text = (
            f"📊 <b>Акция: {ticker}</b>\n\n"
            f"💰 Цена: <b>${data['price']}</b>\n"
            f"📅 За месяц: <code>{data['1m']}%</code>\n"
            f"📅 За год: <code>{data['1y']}%</code>\n\n"
            f"🧠 <b>Прогноз (7 дней):</b>\n"
            f"📈 Рост: {data['up']}%\n"
            f"📉 Падение: {data['down']}%\n\n"
            f"⚠️ <i>Не является финансовой рекомендацией!</i>"
        )
        
        # Генерируем график
        chart_buf = create_chart(data['hist'], ticker)
        photo = types.BufferedInputFile(chart_buf.read(), filename="chart.png")
        
        await message.answer_photo(photo=photo, caption=text, parse_mode="HTML")
        await msg.delete()
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await msg.edit_text("⚠️ Ошибка при получении данных.")

# --- WEB SERVER ДЛЯ RENDER ---
async def handle_web(request): return web.Response(text="Stock Bot is Live")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()
    
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
