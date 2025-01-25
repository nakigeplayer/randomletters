import os
import asyncio
import random
import hashlib
import datetime
from pyrogram import Client, filters
from PIL import Image, ImageDraw, ImageFont

# Función para generar un nombre de archivo de sesión a partir del hash
def get_hashed_session_name(session_name):
    return hashlib.sha256(session_name.encode()).hexdigest()

# Obtener variables de entorno
LOG_TYPE = os.getenv('LOG_TYPE')
LOG = os.getenv('LOG')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
LETTERS = int(os.getenv('LETTERS'))
ADMIN = [int(uid) for uid in os.getenv('ADMIN').split(',')]

# Configuración del cliente de Pyrogram
if LOG_TYPE == 'TOKEN':
    client = Client(f"bot_{LOG}", api_id=API_ID, api_hash=API_HASH, bot_token=LOG)
elif LOG_TYPE == 'SS':
    session_name = get_hashed_session_name(LOG)
    client = Client(session_name, api_id=API_ID, api_hash=API_HASH)

# Función para generar una palabra random
def generate_random_word(length):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=length))

# Función para generar un color hexadecimal random
def generate_hex_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

# Función para crear la imagen según las especificaciones
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

# Enviar mensajes cada 10 minutos en minutos exactos (00, 10, 20, 30, 40, 50)
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

@client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    try:
        print('/start received')  # Depuración
        await message.reply_text('Bot activado. Puedes empezar a recibir mensajes.')
    except Exception as e:
        print(f'Error responding to /start: {e}')

@client.on_message(filters.command("gen") & filters.private)
async def generate_words(client, message):
    try:
        print('/gen received')  # Depuración
        words = [generate_random_word(LETTERS) for _ in range(4)]
        await message.reply_text(', '.join(words))
    except Exception as e:
        print(f'Error responding to /gen: {e}')

@client.on_message(filters.command("sendto") & filters.private)
async def send_to_chat(client, message):
    if message.from_user.id in ADMIN:
        try:
            command, chat_id = message.text.split()
            chat_id = int(chat_id)
            word = generate_random_word(LETTERS)
            print(f'Enviando palabra al chat {chat_id}: {word}')  # Depuración
            await client.send_message(chat_id, word)
            await message.reply_text('Mensaje enviado.')
        except ValueError:
            await message.reply_text('Uso incorrecto: /sendto ChatID')
        except Exception as e:
            print(f'Error sending message to chat {chat_id}: {e}')
    else:
        await message.reply_text('No tienes permisos para usar este comando.')

@client.on_message(filters.command("create") & filters.private)
async def create_image_command(client, message):
    if message.from_user.id in ADMIN:
        try:
            text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "HELLO"
            image_path = create_image(text)
            print(f'Enviando imagen al chat {message.chat.id}')  # Depuración
            await client.send_photo(message.chat.id, image_path)
        except Exception as e:
            print(f'Error creating or sending the image: {e}')
    else:
        await message.reply_text('No tienes permisos para usar este comando.')

# Iniciar tareas del bot
async def main():
    try:
        await client.start()
        print('Bot conectado y listo.')  # Depuración
        asyncio.create_task(send_scheduled_messages())
        await client.idle()
    except Exception as e:
        print(f'Error starting the bot: {e}')

client.run(main())
