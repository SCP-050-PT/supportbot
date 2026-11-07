import telebot

with open("token.txt") as f:
    TOKEN = f.read().strip()

bot = telebot.TeleBot(TOKEN)

# Читаем данные из файла triggers.txt и создаем словарь с триггерами и ответами в формате тригер:ответ построчно
with open('triggers.txt', 'r', encoding='utf-8') as f:
    trigger_responses = {}
    for line in f:
        line = line.strip()
        if not line:
            continue  # пропускаем пустые строки
        trigger, response , chat_id = line.split(':', maxsplit=2)
        # разделяем ответ на абзацы
        response = response.replace('\\n', '\n')
        trigger_responses[(trigger,chat_id)] = response

def send_response(message):
    for trigger_word, chat_id in trigger_responses:
        if trigger_word in message.text and message.chat.id == int(chat_id):
            response = trigger_responses[(trigger_word,chat_id)]
            bot.reply_to(message, response)
            break

# Читаем данные из файла greetings.txt и создаем словарь с приветствиями в формате чат_id:приветствие построчно
with open('triggers.txt', 'r', encoding='utf-8') as f:
    trigger_responses = {}
    for line in f:
        line = line.strip()
        if not line:
            continue  # пропускаем пустые строки
        trigger, response, chat_id = line.split(':', maxsplit=2)
        response = response.replace('\\n', '\n')
        trigger_responses[trigger] = (response,chat_id)

# Словарь для хранения ID отправленных сообщений с приветствиями
bot.sent_greetings = {}

# Обработчик для триггеров
@bot.message_handler(func=lambda message: any(trigger_word in message.text for trigger_word in trigger_responses))
def send_response(message):
    for trigger_word in trigger_responses:
        if trigger_word in message.text and message.chat.id == int(trigger_responses[trigger_word][1]):
            response = trigger_responses[trigger_word][0]
            bot.reply_to(message, response)
            break

# Обработчик для новых участников чата
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_member(message):
    chat_id = message.chat.id
    for member in message.new_chat_members:
        greeting = greetings.get(chat_id)
        if greeting is None:
            continue  # пропускаем чаты без приветствия
        greeting = greeting.format(member=member)
        # Удаляем предыдущее приветствие, если оно есть
        if bot.sent_greetings.get(chat_id):
            deleted_message_id = bot.sent_greetings[chat_id]
            bot.delete_message(chat_id=chat_id, message_id=deleted_message_id)
            print(f'Deleted previous greeting message with ID {deleted_message_id} in chat {chat_id}')
        # Отправляем новое приветствие в ответ на предыдущее приветствие бота (если оно было)
        if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
            sent_message = bot.reply_to(message.reply_to_message, greeting)
        # Иначе отправляем новое приветствие напрямую в чат
        else:
            sent_message = bot.send_message(chat_id, greeting)
        # Запоминаем ID отправленного сообщения с приветствием
        bot.sent_greetings[chat_id] = sent_message.message_id

# Запускаем бота
bot.polling()