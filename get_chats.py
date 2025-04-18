from pyrogram import Client

# Заполните своими учетными данными от my.telegram.org
api_id = 21564722
api_hash = 'a37810f1f9432966784ac36e1df673bd'
# Создание клиента и подключение
app = Client("garmvs", api_id=api_id, api_hash=api_hash)


from pyrogram.enums.chat_type import ChatType
app.start()
for i in list(app.get_dialogs()):
    if i.chat.type in (ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP):
        print(i.chat.id,i.chat.title)
