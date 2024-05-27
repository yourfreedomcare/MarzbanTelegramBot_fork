'''
File includes the main Telegram bot class 
with all the availabe message callbacks and query callbacks 
'''



from telebot import TeleBot
from logger import logger
from database.base import Base, engine
from .utils import *
from database.user import UserRepository
from marzban_api.marzban_service import MarzbanService
import os


class TelegramBot():
    bot = TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))
    Base.metadata.create_all(engine)        
    admin_users = os.getenv('ADMIN_USERS').split(',')


    # Starting point of bot
    @bot.message_handler(commands=['start'])
    def entrypoint(message): 
        try:
            telegram_user_id = retrieve_username(message.from_user)
            logger.info(f"entrypoint -> telegram_user_id {telegram_user_id}")
            user, configurations = UserRepository.get_user(telegram_user_id)

            if user == None or len(configurations) == 0 : 
                if user == None:
                    logger.info(f"chat id {message.chat.id}")
                    UserRepository.create_new_user(telegram_user_id, message.chat.id)
                show_create_configurations_message(TelegramBot.bot, message, messages_content['welcome'].format(breakpoint="\n\n"))
            else:
                create_reply_keyboard_panel(TelegramBot.bot, message.chat.id, messages_content['welcome_back'])
        except Exception: 
            logger.error(f"Exception -> entrypoint: ", exc_info=True)
            TelegramBot.bot.send_message(message.chat.id, messages_content['unexpected_error'])


    # Refresh configs function used only by the Admins 
    @bot.message_handler(commands=['refresh'])
    def refresh_logic(message): 
        try:
            telegram_user_id = retrieve_username(message.from_user)
            if telegram_user_id in TelegramBot.admin_users: 
                TelegramBot.bot.send_message(message.chat.id, messages_content['refresh_started'])
                refresh_configs()
                TelegramBot.bot.send_message(message.chat.id, messages_content['refresh_done'])
            else: 
                TelegramBot.bot.send_message(message.chat.id, messages_content['default_fallback'])
        except Exception: 
            logger.error(f"Exception -> entrypoint: ", exc_info=True)
            TelegramBot.bot.send_message(message.chat.id, messages_content['unexpected_error'])


    # User/Configs Creation
    @bot.callback_query_handler(func=lambda call: call.data in ['configurations'])
    def configurations_callback_query(call):
        try:
            telegram_user_id = retrieve_username(call.from_user)
            configs = UserRepository.get_user_configurations(telegram_user_id)
            if len(configs) > 0: 
                TelegramBot.bot.send_message(call.message.chat.id, messages_content['configs_exist'])
            else:
                user_data, status_code, access_token = MarzbanService.create_marzaban_user(telegram_user_id)

                if status_code == 409: 
                    user_data, status_code = MarzbanService.get_marzaban_user(telegram_user_id, access_token)

                if status_code > 299: 
                    raise Exception("Failed API Call")

                UserRepository.insert_configurations(telegram_user_id, call.message.chat.id, user_data['links'])
                create_reply_keyboard_panel(TelegramBot.bot, call.message.chat.id, messages_content['created_configs'])
        except Exception: 
            logger.error(f"Exception -> configurations_callback_query: ", exc_info=True)
            logger.error(f"API Response -> {user_data} ")
            TelegramBot.bot.send_message(call.message.chat.id, messages_content['unexpected_error'])


    # Configs Retrieval 
    @bot.message_handler(func=lambda message: message.text == '🔑 Получить ключи')
    def get_configurations(message):
        try:
            telegram_user_id = retrieve_username(message.from_user)
            configurations = UserRepository.get_user_configurations(telegram_user_id)
            if len(configurations) > 0:
                prepare_configs_panel(TelegramBot.bot, message.chat.id, configurations)
            else: 
                show_create_configurations_message(TelegramBot.bot, message, messages_content['no_configs'])

        except Exception: 
            logger.error(f"Exception -> get_configurations: ", exc_info=True)
            TelegramBot.bot.send_message(message.chat.id, messages_content['unexpected_error'])

    # Manuals Retrieval 
    @bot.message_handler(func=lambda message: message.text == '🛟 Помощь')
    def get_manuals(message):
        try:
            manuals = messages_content['manuals'].format(link=os.getenv("MANUALS_LINK"), support=os.getenv("SUPPORT_TG"))
            TelegramBot.bot.send_message(message.chat.id, manuals, parse_mode='HTML')
        except Exception: 
            logger.error(f"Exception -> get_manuals: ", exc_info=True)
            TelegramBot.bot.send_message(message.chat.id, messages_content['unexpected_error'])

    # Vless links retrieval 
    @bot.callback_query_handler(func = lambda call: call.message.text == "🌍 Выбери локацию сервера")
    def return_link_callback_query(call): 
        try:
            telegram_user_id = retrieve_username(call.from_user)
            configurations = UserRepository.get_user_configurations(telegram_user_id)
            d = prepare_links_dictionary_rework(configurations)
            if d[call.data]:
                TelegramBot.bot.send_message(call.message.chat.id, messages_content['link_available_1'].format(link=os.getenv("MANUALS_LINK")), parse_mode='HTML')
                TelegramBot.bot.send_message(call.message.chat.id, messages_content['link_available_2'].format(breakpoint="\n\n", link=d[call.data]), parse_mode='Markdown')
            else: 
                TelegramBot.bot.send_message(call.message.chat.id, messages_content['link_unavailable'].format(locatuon=call.data))
        except Exception: 
            logger.error(f"Exception -> return_link_callback_query:", exc_info=True)
            TelegramBot.bot.send_message(call.message.chat.id, messages_content['unexpected_error'])

    # Default fallback for any unrecognized message 
    @bot.message_handler(func=lambda message: True)
    def default_message(message):
        TelegramBot.bot.send_message(message.chat.id, messages_content['default_fallback'])

    def start_bot(self):
        TelegramBot.bot.polling() 
