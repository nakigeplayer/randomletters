import os
import hashlib
import asyncio
import random
import datetime
from telethon import TelegramClient, events
from PIL import Image, ImageDraw, ImageFont

def get_hashed_session_name(session_name):
    return hashlib.sha256(session_name.encode()).hexdigest()

LOG_TYPE = os.getenv('LOG_TYPE')
LOG = os.getenv('LOG')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
LETTERS = int(os.getenv('LETTERS'))
ADMIN = [int(uid) for uid in os.getenv('ADMIN').split(',')]

session_directory = './sessions'
os.makedirs(session_directory, exist_ok=True)

if LOG_TYPE == 'TOKEN':
    client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=LOG)
elif LOG_TYPE == 'SS':
    session_path = os.path.join(session_directory, get_hashed_session_name(LOG))
    open(session_path, 'a').close()
    client = TelegramClient(session_path, API_ID, API_HASH)

def generate_random_word(length):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=length))

def generate_hex_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def create_image(text):
    width, height = 800, 400
    background_color = generate_hex_color()
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_size = 72

    image = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    text = text.upper()
    text_width, text_height = draw.textsize(text, font=font)
    position = ((width - text_width) // 2, (height - text_height) // 2)

    border_width = 2
    for angle in range(0, 360, 45):
        offset_x = border_width * math.cos(math.radians(angle))
        offset_y = border_width * math.sin(math.radians(angle))
        draw.text((position[0] + offset_x, position[1] + offset_y), text, font=font, fill="white")

    draw.text(position, text, font=font, fill="black")

    image.save('output_image.png')
    image.show()
    return 'output_image.png'

async def send_scheduled_messages():
    while True:
        current_time = datetime.datetime.now().time()
        current_minutes = current_time.minute
        next_send_time = (10 - current_minutes % 10) % 10
        await asyncio.sleep(next_send_time * 60)
        word = generate_random_word(LETTERS)
        try:
            await client.send_message(CHANNEL_ID, word)
            print(f'Successfully sent message to {CHANNEL_ID}.')
        except Exception as e:
            print(f'Error sending message to {CHANNEL_ID}: {e}')
        await asyncio.sleep(10 * 60)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    try:
        print('/start received')  # Depuración
        await event.respond('Bot activado. Puedes empezar a recibir mensajes.')
    except Exception as e:
        print(f'Error responding to /start: {e}')

@client.on(events.NewMessage(pattern='/gen'))
async def generate_words(event):
    try:
        print('/gen received')  # Depuración
        words = [generate_random_word(LETTERS) for _ in range(4)]
        await event.respond(', '.join(words))
    except Exception as e:
        print(f'Error responding to /gen: {e}')

@client.on(events.NewMessage(pattern='/sendto'))
async def send_to_chat(event):
    if event.sender_id in ADMIN:
        try:
            command, chat_id = event.raw_text.split()
            chat_id = int(chat_id)
            word = generate_random_word(LETTERS)
            print(f'Enviando palabra al chat {chat_id}: {word}')  # Depuración
            await client.send_message(chat_id, word)
            await event.respond('Mensaje enviado.')
        except ValueError:
            await event.respond('Uso incorrecto: /sendto ChatID')
        except Exception as e:
            print(f'Error sending message to chat {chat_id}: {e}')
    else:
        await event.respond('No tienes permisos para usar este comando.')

@client.on(events.NewMessage(pattern='/create'))
async def create_image_command(event):
    if event.sender_id in ADMIN:
        try:
            text = event.raw_text.split(maxsplit=1)[1] if len(event.raw_text.split()) > 1 else "HELLO"
            image_path = create_image(text)
            print(f'Enviando imagen al chat {event.chat_id}')  # Depuración
            await client.send_file(event.chat_id, image_path)
        except Exception as e:
            print(f'Error creating or sending the image: {e}')
    else:
        await event.respond('No tienes permisos para usar este comando.')

async def main():
    try:
        await client.start()
        await client.connect()
        print('Bot conectado y listo.')  # Depuración
        asyncio.create_task(send_scheduled_messages())
    except Exception as e:
        print(f'Error starting the bot: {e}')

client.loop.run_until_complete(main())
