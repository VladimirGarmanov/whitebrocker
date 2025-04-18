from pyrogram import Client

# Заполните своими учетными данными от my.telegram.org
api_id = 21564722
api_hash = 'a37810f1f9432966784ac36e1df673bd'
# Создание клиента и подключение
app = Client("garmvs", api_id=api_id, api_hash=api_hash)
app.start()
link = [
    "https://t.me/FF_9Gramm",
    "https://t.me/packingBOX_Ff",
    "https://t.me/fbo_ff",
    "https://t.me/efulfillment",
    "https://t.me/bumfull",
    "https://t.me/FBS_FF",
    "https://t.me/FullU2",
    "https://t.me/fulfilment_moskva_akmuradrim",
    "https://t.me/ff_flobas",
    "https://t.me/ifullfilment",
    "https://t.me/Full_Trust_Fulfilment",
    "https://t.me/refulll",
    "https://t.me/mpgroup_fulfillment",
    "https://t.me/dostavka_wb_ozon_ym",
    "https://t.me/OkFulfillment_group",
    "https://t.me/ff_lubercy",
    "https://t.me/fulfilmentspb",
    "https://t.me/skladbot_ff",
    "https://t.me/ff_lite_box",
    "https://t.me/fulfik_ru",
    "https://t.me/fulfillmentRussia",
    "https://t.me/+Anf1M2QfvARhZjEy",
    "https://t.me/FF_Expres",
    "https://t.me/FulForPeople",
    "https://t.me/ffmir",
    "https://t.me/ff_welcome_chat",
    "https://t.me/FulfilmentAkenzy"
]

async def main():
    for chat_url in link:
        try:
            chat_info = await app.get_chat(chat_url)
            chat_id = chat_info.id
            await app.join_chat(chat_id)
            print(f"Присоединился к чату: {chat_url}")
        except Exception as e:
            print(f"Не удалось присоединиться к чату {chat_url}: {e}")

app.run(main())
