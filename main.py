# coding=utf-8
import random
import asyncio
import os
import re
import sqlite3
import time

from pyrogram.enums import ChatAction, MessageEntityType
import openai
from pyrogram import Client, filters

import configparser

from pyrogram.types import MessageEntity

# Создание объекта ConfigParser
config = configparser.ConfigParser()

# Чтение файла config.ini
config.read('config.ini')

openai_api_key = config.get('Config', 'openai_api_key')
api_id = config.get('Config', 'api_id')
api_hash = config.get('Config', 'api_hash')
assistant_id = config.get('Config', 'assistant_id')
text = config.get('Config', 'text')
client = openai.OpenAI(api_key=openai_api_key)
Assistant_ID = assistant_id

# Инициализация Pyrogram Client
app = Client(name="garmvs", api_id=api_id, api_hash=api_hash)

# Инициализация OpenAI
openai.api_key = openai_api_key
price_sent = {}
chat_sessions = {}
# Список пользователей, которым бот уже отправлял сообщения
initiated_users = set()
ice_request = -4259116692

ready_clients = []


async def send_initial_message(user_id):
    messages = [
        "Здравствуйте! Вы в чате нашего ЖК писали. У меня есть возможность купить у застройщика квартиру со скидкой в строящемся корпусе. Вам это будет интересно?"
    ]

    selected_message = random.choice(messages)

    await app.send_message(user_id, text=selected_message)

    thread = client.beta.threads.create()

    chat_sessions[user_id] = thread.id
    price_sent[user_id] = False
    thread = client.beta.threads.create()

    chat_sessions[user_id] = thread.id
    price_sent[user_id] = False
    print('dfjn')
    initiated_users.add(user_id)


def transcript(file):
    audio_file = open(file, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcription.text


def add_user(chat_id):
    thread = client.beta.threads.create()
    chat_sessions[chat_id] = thread.id
    price_sent[chat_id] = False


async def handle_chat_with_gpt(message, messageText):
    print('генерация началась')
    print(message.text)
    thread_id = chat_sessions[message.from_user.username]
    price = price_sent[message.from_user.username]
    message_answer = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=messageText

    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=Assistant_ID,

    )

    time.sleep(10)
    run_status = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run.id
    )

    print(run_status.status)
    while run_status.status == 'in_progress':
        time.sleep(5)
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
    print(run_status.status)
    if run_status.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )

        msg = messages.data[0]
        role = msg.role
        content = msg.content[0].text.value
        print(f"{role.capitalize()}: {content}")
        print(chat_sessions)
        if message.from_user.username not in ready_clients:
            if 'send' in content:
                ready_clients.append(message.from_user.username)
                await app.send_message(chat_id=-4745940045,
                                       text=f"Клиент с ником @{message.from_user.username} готов к завершению сделки   {content}")
                await app.send_message(chat_id=message.chat.id,
                                       text='Я передал ваш контакт, скоро вами свяжутся')
            else:
                await app.send_message(chat_id=message.chat.id, text=content)


keywords_pattern = re.compile(
    r'\b(квартира|купили квартиру|нравится квартира|довольны|долго живете|что нравится|как атмосфера|соседи шумят|есть охрана|можно на парковку|сколько за коммуналку|собак|кошек|уборку подъезда|ДДУ|застройщик|школа|садик|собрание жильцов|за сколько брали|ипотеку|порекомендовали)\b',
    re.IGNORECASE)


@app.on_message(filters.text & filters.regex(keywords_pattern) & ~filters.private)
async def detect_keywords_in_group(client, message):
    print(message.text)
    user_id = message.from_user.username
    if message.from_user.is_bot:
        return
    if user_id not in initiated_users:
        await send_initial_message(user_id)
        await message.forward(-4535578410)
        group_title = message.chat.title
        group_link = f"https://t.me/{message.chat.username}" if message.chat.username else "Ссылка недоступна"
        message_link = message.link if message.link else "Ссылка на сообщение недоступна"
        sender_username = message.from_user.username if message.from_user.username else "Анонимный пользователь"

        match = keywords_pattern.search(message.text)
        detected_keyword = match.group(0) if match else "Неопределенное слово"
        await app.send_message(chat_id=-4535578410,
                               text=f"Сообщение из группы: {group_title} Ссылка на группу: {group_link} Ссылка на сообщение: {message_link} Отправитель: @{sender_username} Обнаруженное слово: {detected_keyword}")
    print(f"Сообщение из группы: {group_title}")
    print(f"Ссылка на группу: {group_link}")
    print(f"Ссылка на сообщение: {message_link}")
    print(f"Отправитель: @{sender_username}")
    print(f"Обнаруженное слово: {detected_keyword}")


@app.on_message(filters.command("stopchat"))
async def stop_chat(client, message):
    user_id = message.from_user.username
    if user_id in initiated_users:
        initiated_users.remove(user_id)
        await message.reply_text("Общение с виртуальным помощником прекращено.")


@app.on_message(filters.command("startchat"))
async def start_chat(client, message):
    user_id = message.from_user.username
    if user_id not in initiated_users:
        initiated_users.add(user_id)
        await message.reply_text("Общение с виртуальным помощником возобновлено.")


@app.on_message(filters.private & ~filters.command("start"))
async def private_message_handler(client, message):
    user_id = message.from_user.username
    if user_id in initiated_users:
        await handle_chat_with_gpt(message, message.text)
    else:
        add_user(user_id)
        await handle_chat_with_gpt(message, message.text)


app.run()
