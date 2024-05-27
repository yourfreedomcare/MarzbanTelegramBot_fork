from database.user import UserRepository
from bot.telegram_bot import TelegramBot
import sys 


# To Execute, run docker-compose exec app bash
# Then run python3 scripts/broadcast.py "Put you message in here" 

telegram_bot = TelegramBot()
message_content = sys.argv[1]
users = UserRepository.get_users()
for user in users: 
    telegram_bot.bot.send_message(user.chat_id, message_content)