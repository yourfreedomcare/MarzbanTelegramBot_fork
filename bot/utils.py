'''
Utils file include all the helper functions user by the 
bot class
'''
from telebot import types
import urllib.parse
from marzban_api.marzban_service import MarzbanService
from database.user import UserRepository
import re, json
import sqlite3


with open('message_content.json', 'r') as file:
    messages_content = json.load(file)

with open('button_content.json', 'r') as file:
    button_content = json.load(file)

def show_create_configurations_message(bot, message, content):
    keyboard = types.InlineKeyboardMarkup()
    create_configs_button = types.InlineKeyboardButton(button_content['Create Configurations'], callback_data='configurations')
    
    keyboard.row(create_configs_button)
    bot.send_message(message.chat.id, content
                     , reply_markup=keyboard)
    

def prepare_configs_panel(bot, chatId, configurations): 
    links_dict = prepare_links_dictionary_rework(configurations)
    keyboard = types.InlineKeyboardMarkup()
    for link in links_dict: 
        button = types.InlineKeyboardButton(link, callback_data=link)
        keyboard.row(button)
    
    bot.send_message(chatId, messages_content['configs_panel'], reply_markup=keyboard)


def create_reply_keyboard_panel(isAdmin, bot, chatId, txtMessage):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Define the buttons
    getConfigs = types.KeyboardButton(button_content['Get Configurations'])
    getManuals = types.KeyboardButton(button_content['Get Manuals'])
    forceUpdate = types.KeyboardButton(button_content['Force Update'])
    refreshConfigs = types.KeyboardButton(button_content['Refresh Configs'])
    broadcast = types.KeyboardButton(button_content['Broadcast'])


    # Add buttons to the keyboard
    keyboard.add(getConfigs, getManuals)
    if isAdmin: 
        keyboard.add(forceUpdate, refreshConfigs, broadcast)

    # Send a message with the reply keyboard
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

def bytes_to_gb(bytes_value):
    return round(bytes_value / (1024 ** 3), 2)

def fetch_marzban_user_data(username):
    conn = sqlite3.connect('db/marzban_db.sqlite3')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, used_traffic, data_limit FROM users WHERE username = ?",
        (username,)
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        status, used_traffic, data_limit = result
        # Replace None with 0 to avoid subtraction error
        used_traffic = used_traffic or 0
        data_limit = data_limit or 0
        return status, used_traffic, data_limit
    return "UNKNOWN", 0, 0

def prepare_links_dictionary_rework(configurations):
    start_idx = "%5B"
    end_idx = "%5D"
    parsed_data_dict = {}

    if not configurations:
        return parsed_data_dict

    marzban_username = configurations[0].telegram_user_id
    status, used_traffic, data_limit = fetch_marzban_user_data(marzban_username)

    for config in configurations: 
        print("config.vless_link", config.vless_link)

        match = re.search(r'sid=#([^&]+)', config.vless_link)
        if not match:
            continue
        spx_value = match.group(1)
        print(spx_value)

        try:
            idx1 = spx_value.index(start_idx)
            idx2 = spx_value.index(end_idx)
            config_title = spx_value[idx1 + len(start_idx): idx2]
            decoded_title = urllib.parse.unquote(urllib.parse.unquote_plus(config_title))
        except ValueError:
            decoded_title = "Unknown"

        data_left_gb = max(0, bytes_to_gb(data_limit - used_traffic))
        final_key = f"{decoded_title} {status.upper()}-{data_left_gb}-GB"
        parsed_data_dict[final_key] = config.vless_link

    return parsed_data_dict

def refresh_configs():
    access_token = MarzbanService.access_token()
    UserRepository.refresh_configs(access_token)

def retrieve_username(user):
    print("retrieve_username: ", user) 
    return str(user.id)