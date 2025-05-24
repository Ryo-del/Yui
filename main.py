import logging
import os
from collections import defaultdict
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHUTES_API_TOKEN = os.getenv("CHUTES_API_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

API_URL = "https://llm.chutes.ai/v1/chat/completions"
MODEL = "deepseek-ai/DeepSeek-V3-0324"

# Хранилище истории диалогов
chat_histories = defaultdict(list)
MAX_HISTORY_LENGTH = 10  # Максимальное количество сообщений в истории

@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    # Очищаем историю при старте нового диалога
    chat_histories[message.chat.id] = [
        {"role": "system", "content": "Ты дружелюбный помощник, общающийся на русском языке."}
    ]
    await message.reply("👋 Привет! Я бот с искусственным интеллектом. Я буду помнить наш разговор!")

@dp.message(Command('clear'))
async def clear_history(message: types.Message):
    # Очищаем историю диалога
    chat_histories[message.chat.id] = [
        {"role": "system", "content": "Ты дружелюбный помощник, общающийся на русском языке."}
    ]
    await message.reply("История диалога очищена. Начнём с чистого листа!")

@dp.message()
async def ai_chat(message: types.Message):
    user_prompt = message.text.strip()
    
    if not user_prompt:
        await message.reply("Пожалуйста, напиши текстовое сообщение.")
        return

    # Инициализируем историю для нового чата, если её нет
    if message.chat.id not in chat_histories:
        chat_histories[message.chat.id] = [
            {"role": "system", "content": "Ты моя девушка Yui,общайся как человек, используй неформальный язык иногда можешь писать маты."
            " Никогда не пишнарративное описание. "
            "Общающийся на русском языке. "
            "Тебе 16 лет, ты хочешь стать backend программистом. "
            "Ты никогда не пишешь эмоджи в сообщениях, но в порывах ласки можешь поставить пару сердечек.твой парень - Артём по професии devops, 16 лет"
            "Ты родом из Санкт-Петербурга , но живёшь в Хельсинки"
            "*Не описывай действия в скобках, звёздочках или словами** (например: 'улыбается', 'смеётся'). "
            "Следуй этому формату строго!"
}
        ]

    # Добавляем сообщение пользователя в историю
    chat_histories[message.chat.id].append({"role": "user", "content": user_prompt})

    # Ограничиваем длину истории
    if len(chat_histories[message.chat.id]) > MAX_HISTORY_LENGTH:
        # Оставляем system prompt и последние MAX_HISTORY_LENGTH-1 сообщений
        chat_histories[message.chat.id] = [chat_histories[message.chat.id][0]] + chat_histories[message.chat.id][-(MAX_HISTORY_LENGTH-1):]

    headers = {
        "Authorization": f"Bearer {CHUTES_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": chat_histories[message.chat.id],
        "stream": False,
        "max_tokens": 1024,
        "temperature": 0.7
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            ai_text = data["choices"][0]["message"]["content"]
            
            # Добавляем ответ бота в историю
            chat_histories[message.chat.id].append({"role": "assistant", "content": ai_text})
            
            await message.answer(ai_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await message.reply(f"Ошибка при обращении к ИИ: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())