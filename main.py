from pyaspeller import YandexSpeller

speller = YandexSpeller()

@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return

    text = message.text
    
    try:
        # 1. Проверка орфографии
        spelled_results = speller.spelled(text)
        # Если ошибок нет, spelled() вернет тот же текст, 
        # но мы сделаем красиво:
        corrected_text = spelled_results if spelled_results else text
        
        # Считаем, были ли правки
        has_errors = "✅ Ошибок не найдено" if text == corrected_text else "❌ Исправлены ошибки"

        # 2. Перевод
        if any(c in "абвгдейёжзийклмнопрстуфхцчшщъыьэюя" for c in text.lower()):
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            direction = "🇷🇺 RU ➡️ 🇺🇸 EN"
        else:
            translated = GoogleTranslator(source='auto', target='ru').translate(text)
            direction = "🇺🇸 EN ➡️ 🇷🇺 RU"
            
        response = (
            f"<b>Оригинал:</b> {text}\n"
            f"<b>Статус:</b> {has_errors}\n"
            f"<b>Текст с исправлениями:</b>\n<code>{corrected_text}</code>\n\n"
            f"<b>{direction}:</b>\n<code>{translated}</code>"
        )
    except Exception as e:
        response = "⚠️ Ошибка при обработке. Попробуй позже."
        logging.error(f"Error: {e}")

    await message.answer(response, parse_mode="HTML")
