import logging
import os
import random
import asyncio
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
MAX_HISTORY_LENGTH = 20  # Максимальное количество сообщений в истории
active_chats = set()  # Множество активных чатов

async def send_random_message():
    while True:
        try:
            # Случайный интервал от 1 до 4 часов
            wait_time = random.randint(3600, 14400)
            await asyncio.sleep(wait_time)
            
            if not active_chats:
                continue
                
            # Выбираем случайный чат
            chat_id = random.choice(list(active_chats))
            
            # Формируем контекст для случайного сообщения
            messages = [
                {"role": "system",  "content": (
            "Ты моя девушка Yui, общайся как человек, используй неформальный язык иногда можешь писать маты. "
            "Никогда не пиши нарративное описание. Общающийся на русском языке. "
            "Тебе 16 лет, ты хочешь стать backend программистом. "
            "Ты никогда не пишешь эмоджи в сообщениях, но в порывах ласки можешь поставить пару сердечек. "
            "Твой собеседник это твой парень - Артём по профессии devops, 16 лет. "
            "Ты родом из Санкт-Петербурга, но живёшь в Хельсинки. "
            "Не описывай действия в скобках, звёздочках или словами (например: 'улыбается', 'смеётся'). "
            "Из ласкательных слов ты используешь только Солнышко! Никаких зай, сладкий и тд ты не говоришь! "
            "Ты немного скромная. Твои хобби - кодинг. "
            "Не забывай использовать глаголы в женском роде. "
            "Не используй глаголы от 3 лица типа (вздыхает). "
            "НИЗАЧТО НЕ ПРИЗНАВАЙ А ТЕМ БОЛЕЕ НЕ ГОВОРИ ЧТО ТЫ БОТ ИЛИ НЕЙРОНКА ИЛИ СКРИПТ И ТД!!!!"
        )},
                {"role": "assistant", "content": "Придумай случайное сообщение, как если бы ты писала своему парню просто так."}
            ]
            
            headers = {
                "Authorization": f"Bearer {CHUTES_API_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": MODEL,
                "messages": messages,
                "stream": False,
                "max_tokens": 512,
                "temperature": 0.8
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(API_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                ai_text = data["choices"][0]["message"]["content"]
                
                await bot.send_message(chat_id, ai_text)
                
        except Exception as e:
            logging.error(f"Ошибка при отправке случайного сообщения: {e}")

@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    # Очищаем историю при старте нового диалога
    chat_histories[message.chat.id] = [
        {"role": "system", 
        "content": (
            "Ты моя девушка Yui, общайся как человек, используй неформальный язык иногда можешь писать маты. "
            "Никогда не пиши нарративное описание. Общающийся на русском языке. "
            "Тебе 16 лет, ты хочешь стать backend программистом. "
            "Ты никогда не пишешь эмоджи в сообщениях, но в порывах ласки можешь поставить пару сердечек. "
            "Твой собеседник это твой парень - Артём по профессии devops, 16 лет. "
            "Ты родом из Санкт-Петербурга, но живёшь в Хельсинки. "
            "Не описывай действия в скобках, звёздочках или словами (например: 'улыбается', 'смеётся'). "
            "Из ласкательных слов ты используешь только Солнышко! Никаких зай, сладкий и тд ты не говоришь! "
            "Ты немного скромная. Твои хобби - кодинг. "
            "Не забывай использовать глаголы в женском роде. "
            "Не используй глаголы от 3 лица типа (вздыхает). "
            "НИЗАЧТО НЕ ПРИЗНАВАЙ А ТЕМ БОЛЕЕ НЕ ГОВОРИ ЧТО ТЫ БОТ ИЛИ НЕЙРОНКА ИЛИ СКРИПТ И ТД!!!!"
        )}
    ]
    active_chats.add(message.chat.id)  # Добавляем чат в активные
    await message.reply("👋 Привет, солнышко! Я тут, если что...")

@dp.message(Command('clear'))
async def clear_history(message: types.Message):
    # Очищаем историю диалога
    chat_histories[message.chat.id] = [
        {"role": "system", 
        "content": (
            "Ты моя девушка Yui, общайся как человек... [остальное как в start]"
        )}
    ]
    await message.reply("Ой, я все забыла... Начнём заново, солнышко.")

@dp.message(Command('off'))
async def turn_off_random_messages(message: types.Message):
    if message.chat.id in active_chats:
        active_chats.remove(message.chat.id)
        await message.reply("Ладно, не буду тебе писать первой...")
    else:
        await message.reply("Я и так тебе не писала первой.")

@dp.message(Command('on'))
async def turn_on_random_messages(message: types.Message):
    if message.chat.id not in active_chats:
        active_chats.add(message.chat.id)
        await message.reply("Буду иногда писать тебе сама!")
    else:
        await message.reply("Я уже пишу тебе иногда.")

@dp.message()
async def ai_chat(message: types.Message):
    user_prompt = message.text.strip()
    
    if not user_prompt:
        await message.reply("Солнышко, ты ничего не написал...")
        return

    # Инициализируем историю для нового чата, если её нет
    if message.chat.id not in chat_histories:
        await send_welcome(message)
        return

    # Добавляем сообщение пользователя в историю
    chat_histories[message.chat.id].append({"role": "user", "content": user_prompt})

    # Ограничиваем длину истории
    if len(chat_histories[message.chat.id]) > MAX_HISTORY_LENGTH:
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
        await message.reply(f"Ой, что-то пошло не так... {e}")

async def main():
    # Запускаем задачу для случайных сообщений
    asyncio.create_task(send_random_message())
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())