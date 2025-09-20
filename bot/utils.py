'''
Utils file include all the helper functions user by the 
bot class
'''
from telebot import types
import urllib.parse
from marzban_api.marzban_service import MarzbanService
from database.user import UserRepository
import re, json

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
    return str(user.id)