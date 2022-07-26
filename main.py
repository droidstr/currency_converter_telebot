import telebot
import extensions
from config import TELEGRAM_TOKEN

converter = extensions.Converter()

bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    reply = '''Чтобы узнать курс валюты, отправьте сообщени в формате '''\
    '''<имя валюты, цену которой вы хотите узнать> '''\
    '''<имя валюты, в которой нужно узнать цену первой валюты> '''\
    '''<количество первой валюты>. '''\
    '''Чтобы узнать список поддерживаемых валют, используйте команду /values'''
    bot.reply_to(message, reply)


@bot.message_handler(commands=['values'])
def handle_start_help(message):
    reply = 'Доступные валюты:\n' + str(converter)
    bot.reply_to(message, reply)


@bot.message_handler(content_types=['text'])
def handle_docs_audio(message):
    reply = converter.get_price(message.text)
    bot.reply_to(message, reply)


bot.polling()
