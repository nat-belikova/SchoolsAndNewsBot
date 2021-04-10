import os
import telebot
import web_parser
from flask import Flask, request

token = os.environ.get('TOKEN')
os.chdir('bot')

bot = telebot.TeleBot(token)
server = Flask(__name__)


@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.send_message(message.chat.id, 'Привет! Я Школьный бот.\n'
                                      'Я отслеживаю новости на сайтах школ, чтобы вы ничего не пропустили :)\n'
                                      'Подробнее обо мне: /info\n'
                                      'Команды, которые я понимаю: /commands\n'
                                      'Список школ: /schools\n'
                                      'Новости какой школы вы хотите узнать?')


@bot.message_handler(commands=['info'])
def cmd_info(message):
    with open('laptop.jpg', 'rb') as pic:
        bot.send_photo(message.chat.id, pic)
    bot.send_message(message.chat.id, 'Я Школьный бот :)\n'
                                      'Я отслеживаю новости на официальных и неофициальных сайтах школ Москвы и '
                                      'показываю вам последние 10 новостей.')
    bot.send_message(message.chat.id, 'Полужирным шрифтом я выделяю информацию, которая может быть интересна '
                                      'поступающим (дни открытых дверей, регистрация на экзамены и сами экзамены). '
                                      'Пока не идеально, но я очень стараюсь!')
    bot.send_message(message.chat.id, 'Сейчас я мониторю следующие школы: /schools\n'
                                      'Команды, которые я понимаю: /commands\n'
                                      'Вернуться в начало: /start')


@bot.message_handler(commands=['schools'])
def cmd_schools(message):
    bot.send_message(message.chat.id, ', '.join(web_parser.school_list))


@bot.message_handler(commands=['commands'])
def cmd_commands(message):
    bot.send_message(message.chat.id, '/start - начать сначала\n'
                                      '/info - информация обо мне\n'
                                      '/schools - список школ, которые я мониторю\n'
                                      '/commands - список команд, которые я понимаю\n\n'
                                      'Введите номер школы из списка /schools, чтобы почитать ее новости.')


@bot.message_handler(func=lambda message: message.text.strip().lower() in web_parser.school_list)
def cmd_show_school_info(message):
    message_text = message.text.strip().lower()
    if len([site for site in web_parser.websites if site['school'] == message_text
                                                    and site['type'].endswith('_selenium')]) > 0:
        with open('waiting.jpg', 'rb') as pic:
            bot.send_photo(message.chat.id, pic)
        bot.send_message(message.chat.id, 'Подождите немного, я скоро отвечу :)')
    school_info_text = web_parser.school_info(message_text)
    if school_info_text == '':
        bot.send_message(message.chat.id, 'Я не смог найти новости этой школы :(')
    else:
        bot.send_message(message.chat.id, school_info_text, disable_web_page_preview=True, parse_mode='HTML')
    bot.send_message(message.chat.id, 'Вы можете почитать новости другой школы из списка /schools\n'
                                      'Вернуться в начало: /start')


@bot.message_handler(func=lambda message: True)
def cmd_other(message):
    bot.send_message(message.chat.id, 'Ой.\n'
                                      'К сожалению, я вас не понимаю.\n'
                                      'Пожалуйста, укажите номер школы из списка /schools, чтобы почитать ее новости.\n'
                                      'Также вы можете просмотреть информацию обо мне /info и мои команды /commands')


@server.route('/' + token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://schools-and-news-bot.herokuapp.com/' + token)
    return "!", 200


if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
    bot.infinity_polling()
