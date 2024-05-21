from telebot import TeleBot
from database.user import UserRepository
from bot.telegram_bot import TelegramBot


telegram_bot = TelegramBot()
message_content = 'test message content'
users = UserRepository.get_users()
for user in users: 
    telegram_bot.bot.send_message(user.chat_id, message_content)