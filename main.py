import logging
import asyncio
import os
import io
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web

# --- НАСТРОЙКИ ---
# Твой токен бота
TOKEN = "8354164344:AAGfLAdD6_tRY6wFc5_2gerCTZ9HIy-wBjU"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЛОГИКА ПОЛУЧЕНИЯ ДАННЫХ ---
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Берем данные за год для расчетов и графика
        hist = stock.history(period="1y")
        
        if hist.empty or len(hist) < 21:
            return None
        
        current_price = hist['Close'].iloc[-1]
        
        # Расчет изменений в процентах
        # 5 рабочих дней ~ 1 неделя, 21 день ~ 1 месяц
        change_1w = ((current_price - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100
        change_1m = ((current_price - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) * 100
        change_1y = ((current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
        
        # Прогноз на основе скользящей средней (SMA)
        sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        prob_up = 65 if current_price > sma_20 else 35
        prob_down = 100 - prob_up
        
        return {
            "price": round(current_price, 2),
            "1w": round(change_1w, 1),
            "1m": round(change_1m, 1),
            "1y": round(change_1y, 1),
            "up": prob_up,
            "down": prob_down,
            "hist": hist,
            "currency": stock.info.get('currency', '$')
        }
    except Exception as e:
        logging.error(f"Ошибка yfinance для {ticker}: {e}")
        return None

# --- ГЕНЕРАЦИЯ ГРАФИКА ---
def create_chart(hist, ticker):
    plt.figure(figsize=(10, 5))
    plt.plot(hist.index, hist['Close'], color='#007AFF', linewidth=2)
    plt.title(f"Динамика цен {ticker} (за 1 год)", fontsize=14)
    plt.xlabel("Дата")
    plt.ylabel("Цена закрытия")
    plt.grid(True, linestyle='--', alpha=0.7)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "📈 <b>Добро пожаловать в Stock Bot!</b>\n\n"
        "Я помогу тебе следить за акциями.\n"
        "Просто отправь мне <b>тикер</b> (например: <code>AAPL</code>, <code>TSLA</code>, <code>NVDA</code>).\n\n"
        "Для акций РФ добавь суффикс <b>.ME</b> (например: <code>GAZP.ME</code>).",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def handle_stock(message: types.Message):
    ticker = message.text.upper().strip()
    
    # Игнорируем команды и старые кнопки
    if ticker.startswith("/") or "СТАТИСТИКА" in ticker or "ПОМОЩЬ" in ticker:
        return

    status_msg = await message.answer(f"🔍 Анализирую данные для <b>{ticker}</b>...", parse_mode="HTML")
    
    data = await asyncio.to_thread(get_stock_data, ticker)
    
    if not data:
        return await status_msg.edit_text(
            f"❌ Не удалось найти данные для <b>{ticker}</b>.\n"
            f"Проверь правильность написания тикера.",
            parse_mode="HTML"
        )
    
    try:
        # Текст ответа
        text = (
            f"📊 <b>Акция: {ticker}</b>\n\n"
            f"💰 Текущая цена: <b>{data['price']} {data['currency']}</b>\n\n"
            f"📅 За неделю: <code>{'+' if data['1w'] > 0 else ''}{data['1w']}%</code>\n"
            f"📅 За месяц: <code>{'+' if data['1m'] > 0 else ''}{data['1m']}%</code>\n"
            f"📅 За год: <code>{'+' if data['1y'] > 0 else ''}{data['1y']}%</code>\n\n"
            f"🧠 <b>Прогноз (7 дней):</b>\n"
            f"📈 Вероятность роста: {data['up']}%\n"
            f"📉 Вероятность падения: {data['down']}%\n\n"
            f"⚠️ <i>Не является финансовой рекомендацией!</i>"
        )
        
        # Создаем и отправляем график
        chart_buf = await asyncio.to_thread(create_chart, data['hist'], ticker)
        photo = types.BufferedInputFile(chart_buf.read(), filename=f"{ticker}_chart.png")
        
        await message.answer_photo(photo=photo, caption=text, parse_mode="HTML")
        await status_msg.delete()
        
    except Exception as e:
        logging.error(f"Ошибка отправки данных для {ticker}: {e}")
        await status_msg.edit_text("⚠️ Произошла ошибка при подготовке отчета.")

# --- WEB SERVER (ЧТОБЫ RENDER НЕ УСЫПЛЯЛ) ---
async def handle_web(request):
    return web.Response(text="Stock Bot is active!")

async def main():
    # Настройка веб-сервера для Render
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    
    # Запуск бота
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
