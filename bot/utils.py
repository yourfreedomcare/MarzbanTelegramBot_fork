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

with open('message_content.json', 'r') as file:
    messages_content = json.load(file)

with open('button_content.json', 'r') as file:
    button_content = json.load(file)

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

@DeprecationWarning
def prepare_links_dictionary(configurations):
    pattern = r'%5B([^%]+)%5D'
    parsed_data_dict = {}
    for config in configurations:
        if 'vless' in config.vless_link: 
            match = re.search(pattern, config.vless_link)
            if match:
                parsed_data = match.group(1)
                parsed_data_dict[parsed_data] = config.vless_link
    return parsed_data_dict

def prepare_links_dictionary_rework(configurations):
    start_idx = "%5B"
    end_idx = "%5D"
    parsed_data_dict = {}

    for config in configurations: 
        logger.info(f"Preparing Vless Link: {config.vless_link}")
        spx_value = re.search(r'sid=#([^&]+)', config.vless_link).group(1)
        logger.info(spx_value)

        try:
            idx1 = spx_value.index(start_idx)
            idx2 = spx_value.index(end_idx)
            config_title = spx_value[idx1 + len(start_idx): idx2]
            decoded_title = urllib.parse.unquote(urllib.parse.unquote_plus(config_title))
        except ValueError:
            decoded_title = "Unknown"

        parsed_data_dict[decoded_title] = config.vless_link

    logger.info(f"parsed_data_dict: {parsed_data_dict}")
    return parsed_data_dict

def refresh_configs():
    access_token = MarzbanService.access_token()
    UserRepository.refresh_configs(access_token)

def retrieve_username(user):
    logger.info(f"retrieve_username: {user}") 
    return str(user.id)
