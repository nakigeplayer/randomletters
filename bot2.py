import os
import asyncio
import random
import datetime
import math
from telethon import TelegramClient, events
from PIL import Image, ImageDraw, ImageFont

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

# Función para generar un color hexadecimal random
def generate_hex_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

# Función para crear la imagen según las especificaciones
def create_image(text):
    width, height = 800, 400  # Dimensiones de la imagen
    background_color = generate_hex_color()
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Fuente predeterminada de Pillow
    font_size = 72

    # Crear imagen con fondo de color random
    image = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)
    
    # Obtener tamaño del texto y calcular posición
    text = text.upper()  # Convertir texto a mayúsculas
    text_width, text_height = draw.textsize(text, font=font)
    position = ((width - text_width) // 2, (height - text_height) // 2)

    # Dibujar borde blanco
    border_width = 2
    for angle in range(0, 360, 45):  # Relleno del borde en todas las direcciones
        offset_x = border_width * math.cos(math.radians(angle))
        offset_y = border_width * math.sin(math.radians(angle))
        draw.text((position[0] + offset_x, position[1] + offset_y), text, font=font, fill="white")

    # Dibujar el texto en negro
    draw.text(position, text, font=font, fill="black")

    # Guardar o mostrar la imagen
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
            await event.respond('Uso incorrecto: /sendto ChatID')
    else:
        await event.respond('No tienes permisos para usar este comando.')

# Manejar el comando para crear y enviar una imagen
@client.on(events.NewMessage(pattern='/create'))
async def create_image_command(event):
    if event.sender_id in ADMIN:
        text = event.raw_text.split(maxsplit=1)[1] if len(event.raw_text.split()) > 1 else "HELLO"
        image_path = create_image(text)
        await client.send_file(event.chat_id, image_path)
    else:
        await event.respond('No tienes permisos para usar este comando.')

# Iniciar tareas del bot
async def main():
    await client.connect()
    asyncio.create_task(send_scheduled_messages())

client.loop.run_until_complete(main())
