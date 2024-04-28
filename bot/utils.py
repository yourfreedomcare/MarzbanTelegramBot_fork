'''
Utils file include all the helper functions user by the 
bot class
'''
from telebot import types
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
    links_dict = prepare_links_dictionary(configurations)
    keyboard = types.InlineKeyboardMarkup()
    for link in links_dict: 
        button = types.InlineKeyboardButton(link, callback_data=link)
        keyboard.row(button)
    
    bot.send_message(chatId, messages_content['configs_panel'], reply_markup=keyboard)


def create_reply_keyboard_panel(bot, chatId, txtMessage):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Define the buttons
    button1 = types.KeyboardButton(button_content['Get Configurations'])
    button2 = types.KeyboardButton(button_content['Get Manuals'])
    # Add buttons to the keyboard
    keyboard.add(button1, button2)
    
    # Send a message with the reply keyboard
    bot.send_message(chatId, txtMessage, reply_markup=keyboard)


def prepare_links_dictionary(configurations):
    pattern = r'spx=#([^%]+)'
    parsed_data_dict = {}
    for config in configurations:
        if 'vless' in config.vless_link: 
            match = re.search(pattern, config.vless_link)
            if match:
                parsed_data = match.group(1)
                parsed_data_dict[parsed_data] = config.vless_link

    return parsed_data_dict

def refresh_configs():
    access_token = MarzbanService.access_token()
    UserRepository.refresh_configs(access_token)

def retrieve_username(user): 
    return str(user.id)