import os
import asyncio
import random
import datetime
from telethon import TelegramClient, events

# Obtener variables de entorno
LOG_TYPE = os.getenv('LOG_TYPE')
LOG = os.getenv('LOG')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
LETTERS = int(os.getenv('LETTERS'))
ADMIN = [int(uid) for uid in os.getenv('ADMIN').split(',')]

# Inicializar el cliente de Telethon basado en LOG_TYPE
if LOG_TYPE == 'TOKEN':
    client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=LOG)
elif LOG_TYPE == 'SS':
    client = TelegramClient(LOG, API_ID, API_HASH)

# Función para generar una palabra random
def generate_random_word(length):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=length))

# Enviar mensajes cada 10 minutos en minutos exactos (00, 10, 20, 30, 40, 50)
async def send_scheduled_messages():
    while True:
        current_time = datetime.datetime.now().time()
        current_minutes = current_time.minute
        next_send_time = (10 - current_minutes % 10) % 10
        await asyncio.sleep(next_send_time * 60)
        word = generate_random_word(LETTERS)
        await client.send_message(CHANNEL_ID, word)
        await asyncio.sleep(10 * 60)

# Manejar comandos específicos
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Bot activado. Puedes empezar a recibir mensajes.')

@client.on(events.NewMessage(pattern='/gen'))
async def generate_words(event):
    words = [generate_random_word(LETTERS) for _ in range(4)]
    await event.respond(', '.join(words))

@client.on(events.NewMessage(pattern='/sendto'))
async def send_to_chat(event):
    if event.sender_id in ADMIN:
        try:
            command, chat_id = event.raw_text.split()
            chat_id = int(chat_id)
            word = generate_random_word(LETTERS)
            await client.send_message(chat_id, word)
            await event.respond('Mensaje enviado.')
        except ValueError:
            await event.respond('Uso incorrecto: /sendto CHatID')
    else:
        await event.respond('No tienes permisos para usar este comando.')

# Iniciar tareas del bot
async def main():
    await client.connect()
    asyncio.create_task(send_scheduled_messages())

client.loop.run_until_complete(main())
