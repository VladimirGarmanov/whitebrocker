# coding=utf-8
import random
import asyncio
import os
import re
import sqlite3
import time
import configparser

from pyrogram.enums import ChatAction, MessageEntityType
from pyrogram import Client, filters
from pyrogram.types import MessageEntity
import openai

# --- Чтение конфига ---
config = configparser.ConfigParser()
config.read('config.ini')
openai_api_key = config.get('Config', 'openai_api_key')
api_id = config.get('Config', 'api_id')
api_hash = config.get('Config', 'api_hash')
assistant_id = config.get('Config', 'assistant_id')

# --- Инициализация Pyrogram и OpenAI ---
app = Client(name="garmvs", api_id=api_id, api_hash=api_hash)
openai.api_key = openai_api_key
client = openai.OpenAI(api_key=openai_api_key)
Assistant_ID = assistant_id

# --- Глобальные структуры ---
initiated_users = set()         # те, кому бот уже писал
disconnected_accounts = set()   # от этих аккаунтов ИИ «отключился»
price_sent = {}
chat_sessions = {}
ready_clients = []

ice_request = -4259116692

# Шаблон ключевых слов для групп
keywords_pattern = re.compile(
    r'\b(квартира|купили квартиру|нравится квартира|довольны|долго живете|что нравится|как атмосфера|соседи шумят|есть охрана|можно на парковку|сколько за коммуналку|собак|кошек|уборку подъезда|ДДУ|застройщик|школа|садик|собрание жильцов|за сколько брали|ипотеку|порекомендовали)\b',
    re.IGNORECASE
)

# Отправка стартового сообщения в ЛС
async def send_initial_message(user_id):
    messages = [
        "Здравствуйте! Вы в чате нашего ЖК писали. У меня есть возможность купить у застройщика квартиру со скидкой в строящемся корпусе. Вам это будет интересно?"
    ]
    await app.send_message(user_id, random.choice(messages))
    thread = client.beta.threads.create()
    chat_sessions[user_id] = thread.id
    price_sent[user_id] = False
    initiated_users.add(user_id)

def add_user(chat_id):
    thread = client.beta.threads.create()
    chat_sessions[chat_id] = thread.id
    price_sent[chat_id] = False

def transcript(file):
    audio_file = open(file, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcription.text

# Обработка диалога с GPT
async def handle_chat_with_gpt(message, messageText):
    me = await app.get_me()
    user_key = message.from_user.username

    # 1) Если бот сам себе пишет — «отключаемся»
    if message.from_user.id == me.id:
        disconnected_accounts.add(user_key)
        initiated_users.discard(user_key)
        return

    # 2) Если аккаунт уже отключён — игнорируем
    if user_key in disconnected_accounts:
        return

    # 3) Стандартная логика отправки в threads API
    thread_id = chat_sessions.get(user_key)
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=messageText
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=Assistant_ID,
    )
    # Ожидаем завершения
    while True:
        time.sleep(5)
        status = client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run.id
        ).status
        if status != 'in_progress':
            break

    if status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        content = messages.data[0].content[0].text.value

        if user_key not in ready_clients and 'send' in content:
            ready_clients.append(user_key)
            await app.send_message(
                chat_id=-4745940045,
                text=f"Клиент @{user_key} готов к завершению сделки: {content}"
            )
            await app.send_message(
                chat_id=message.chat.id,
                text='Я передал ваш контакт, скоро вами свяжутся'
            )
        else:
            await app.send_message(chat_id=message.chat.id, text=content)

# Детект ключевых слов в группах
@app.on_message(filters.text & filters.regex(keywords_pattern) & ~filters.private)
async def detect_keywords_in_group(client, message):
    me = await client.get_me()
    user_key = message.from_user.username

    # Если бот сам себе написал или аккаунт «отключён» — выходим
    if message.from_user.id == me.id or user_key in disconnected_accounts:
        return

    if message.from_user.is_bot:
        return

    if user_key not in initiated_users:
        await send_initial_message(user_key)
        await message.forward(-4535578410)

        group_title = message.chat.title
        group_link = f"https://t.me/{message.chat.username}" if message.chat.username else "ссылка недоступна"
        message_link = message.link or "ссылка на сообщение недоступна"
        sender = f"@{user_key}" if user_key else "аноним"
        word = keywords_pattern.search(message.text).group(0)

        await app.send_message(
            chat_id=-4535578410,
            text=(
                f"Сообщение из группы «{group_title}»\n"
                f"Ссылка на группу: {group_link}\n"
                f"Ссылка на сообщение: {message_link}\n"
                f"Отправитель: {sender}\n"
                f"Ключевое слово: {word}"
            )
        )

# /stopchat
@app.on_message(filters.command("stopchat"))
async def stop_chat(client, message):
    user_key = message.from_user.username
    initiated_users.discard(user_key)
    await message.reply_text("Общение с виртуальным помощником прекращено.")

# /startchat
@app.on_message(filters.command("startchat"))
async def start_chat(client, message):
    user_key = message.from_user.username
    if user_key not in disconnected_accounts:
        initiated_users.add(user_key)
        await message.reply_text("Общение с виртуальным помощником возобновлено.")
    else:
        await message.reply_text("Невозможно возобновить: аккаунт отключён.")

# Приватные сообщения
@app.on_message(filters.private & ~filters.command("start"))
async def private_message_handler(client, message):
    me = await client.get_me()
    user_key = message.from_user.username

    # 1) Если бот сам себе написал — «отключаемся»
    if message.from_user.id == me.id:
        disconnected_accounts.add(user_key)
        initiated_users.discard(user_key)
        return

    # 2) Если аккаунт в чёрном списке — игнор
    if user_key in disconnected_accounts:
        return

    # 3) Если пользователь уже инициализирован — обрабатываем
    if user_key in initiated_users:
        await handle_chat_with_gpt(message, message.text)
    else:
        add_user(user_key)
        await handle_chat_with_gpt(message, message.text)

if __name__ == "__main__":
    app.run()