'''
Utils file includes all the helper functions used by the bot class.
'''

import os
from telebot import types
import urllib.parse
from marzban_api.marzban_service import MarzbanService
from database.user import UserRepository
from database.base import MarzbanSession
import re
import json
from sqlalchemy import text
from logger import logger

CRYPTO_ADDRESSES = {
    'btc': {'network': 'Bitcoin', 'address': os.getenv("BTC_ADDRESS")},
    'ltc': {'network': 'Litecoin', 'address': os.getenv("LTC_ADDRESS")},
    'usdt_erc': {'network': 'USDT (ERC-20)', 'address': os.getenv("USDT_ERC_ADDRESS")},
    'usdt_trc': {'network': 'USDT (TRC-20)', 'address': os.getenv("USDT_TRC_ADDRESS")},
}

def get_crypto_address_info(coin_key):
    return CRYPTO_ADDRESSES.get(coin_key)

CONTENT_DIR = 'content'

with open(os.path.join(CONTENT_DIR, 'message_content.json'), 'r') as file:
    messages_content = json.load(file)

with open(os.path.join(CONTENT_DIR, 'button_content.json'), 'r') as file:
    button_content = json.load(file)

with open(os.path.join(CONTENT_DIR, 'donations_content.json'), 'r') as file:
    donations_content = json.load(file)

def show_create_configurations_message(bot, message, content):
    keyboard = types.InlineKeyboardMarkup()
    create_configs_button = types.InlineKeyboardButton(button_content['Create Configurations'], callback_data='configurations')
    keyboard.row(create_configs_button)
    bot.send_message(message.chat.id, content, reply_markup=keyboard)

def bytes_to_gb(bytes_value):
    return round(bytes_value / (1024 ** 3), 2)

def fetch_marzban_user_data(username):
    session = MarzbanSession()
    try:
        result = session.execute(
            text("SELECT status, used_traffic, data_limit FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()

        if result:
            status, used_traffic, data_limit = result
            used_traffic = used_traffic or 0
            data_limit = data_limit or 0
            return status, used_traffic, data_limit
        return "UNKNOWN", 0, 0
    except Exception as e:
        logger.info(f"Marzban DB Error: {e}")
        return "ERROR", 0, 0
    finally:
        session.close()

def prepare_configs_panel(bot, chatId, configurations): 
    links_dict = prepare_links_dictionary_rework(configurations)
    keyboard = types.InlineKeyboardMarkup()
    for link in links_dict: 
        button = types.InlineKeyboardButton(link, callback_data=link)
        keyboard.row(button)
        logger.info(f"Adding button for link: {link}")
    bot.send_message(chatId, messages_content['configs_panel'], reply_markup=keyboard)

def create_reply_keyboard_panel(isAdmin, bot, chatId, txtMessage):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    getConfigs = types.KeyboardButton(button_content['Get Configurations'])
    getManuals = types.KeyboardButton(button_content['Get Manuals'])
    forceUpdate = types.KeyboardButton(button_content['Force Update'])
    refreshConfigs = types.KeyboardButton(button_content['Refresh Configs'])
    broadcast = types.KeyboardButton(button_content['Broadcast'])
    donate = types.KeyboardButton(button_content['Donate'])

    keyboard.add(getConfigs, getManuals, donate)
    if isAdmin: 
        keyboard.add(forceUpdate, refreshConfigs, broadcast)

    bot.send_message(chatId, txtMessage, reply_markup=keyboard)

def create_needs_update_message(bot, chat_id):
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(button_content['update'], callback_data='update')
    keyboard.add(button)
    bot.send_message(chat_id, messages_content['update'], reply_markup=keyboard)

def prepare_links_dictionary_rework(configurations):
    parsed_data_dict = {}
    for config in configurations:
        match = re.search(r'#%5B(.*?)%5D', config.vless_link)
        if match:
            encoded_config_title = match.group(1)
            config_title = urllib.parse.unquote(urllib.parse.unquote_plus(encoded_config_title))
            parsed_data_dict[config_title] = config.vless_link
        else:
            print(f"Cant find data in link: {config.vless_link}")

    return parsed_data_dict

def refresh_configs():
    access_token = MarzbanService.access_token()
    UserRepository.refresh_configs(access_token)

def retrieve_username(user):
    logger.info(f"retrieve_username: {user}") 
    return str(user.id)
