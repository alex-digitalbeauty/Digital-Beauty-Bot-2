import os
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Константа курса
USD_UAH = 49

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📊 Розрахувати окупність апарату"),
        types.KeyboardButton("👨‍💼 Звʼязок з менеджером")
    )
    return markup

# Старт
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Обери дію:", reply_markup=main_menu())

# Контакт менеджера
@bot.message_handler(func=lambda m: m.text == "👨‍💼 Звʼязок з менеджером")
def contact_manager(message):
    bot.send_message(message.chat.id, "Для звʼязку з менеджером пишіть сюди: @alex_digital_beauty")

# Выбор аппарата
@bot.message_handler(func=lambda m: m.text == "📊 Розрахувати окупність апарату")
def choose_device(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("IPL A-Tone", "Finexel CO2", "10THERMA", "⬅️ Повернутись в меню")
    bot.send_message(message.chat.id, "Оберіть апарат:", reply_markup=markup)

# Словарь для хранения данных пользователя
user_data = {}

# Вопросы по шагам
def ask_question_step(chat_id, step):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if step == 1:
        markup.add("27000€", "Ввести іншу вартість", "⬅️ Повернутись в меню")
        bot.send_message(chat_id, "Вартість апарату:", reply_markup=markup)
    elif step == 2:
        markup.add("200 процедур", "Ввести іншу кількість", "⬅️ Повернутись в меню")
        bot.send_message(chat_id, "Кількість процедур на місяць:", reply_markup=markup)
    elif step == 3:
        markup.add("3500 грн", "Ввести іншу вартість", "⬅️ Повернутись в меню")
        bot.send_message(chat_id, "Вартість процедури:", reply_markup=markup)
    elif step == 4:
        markup.add("15% від вартості послуги", "Введіть інший %", "⬅️ Повернутись в меню")
        bot.send_message(chat_id, "Заробітня плата фахівця:", reply_markup=markup)
    user_data[chat_id]['step'] = step

# Обработка выбора аппарата
@bot.message_handler(func=lambda m: m.text in ["IPL A-Tone", "Finexel CO2", "10THERMA"])
def device_selected(message):
    chat_id = message.chat.id
    user_data[chat_id] = {"device": message.text}
    if message.text == "IPL A-Tone":
        ask_question_step(chat_id, 1)

# Универсальный обработчик всех ответов
@bot.message_handler(func=lambda m: True)
def handle_answers(message):
    chat_id = message.chat.id

    # Кнопка "Вернуться в меню" работает всегда
    if message.text == "⬅️ Повернутись в меню":
        bot.send_message(chat_id, "Повертаємось в меню:", reply_markup=main_menu())
        user_data.pop(chat_id, None)
        return

    # Если пользователь не в процессе — игнорируем
    if chat_id not in user_data:
        return

    step = user_data[chat_id].get('step', 0)

    # Шаг 1 — стоимость аппарата
    if step == 1:
        if message.text == "27000€":
            user_data[chat_id]['cost'] = 27000
            ask_question_step(chat_id, 2)
        else:
            try:
                val = float(message.text.replace("€", ""))
                user_data[chat_id]['cost'] = val
                ask_question_step(chat_id, 2)
            except:
                bot.send_message(chat_id, "Помилка! Введіть число (€):")
    # Шаг 2 — количество процедур
    elif step == 2:
        if message.text == "200 процедур":
            user_data[chat_id]['count'] = 200
            ask_question_step(chat_id, 3)
        else:
            try:
                val = int(message.text)
                user_data[chat_id]['count'] = val
                ask_question_step(chat_id, 3)
            except:
                bot.send_message(chat_id, "Помилка! Введіть число процедур:")
    # Шаг 3 — стоимость процедуры
    elif step == 3:
        if message.text == "3500 грн":
            user_data[chat_id]['price'] = 3500
            ask_question_step(chat_id, 4)
        else:
            try:
                val = float(message.text.replace("грн","").replace(" ",""))
                user_data[chat_id]['price'] = val
                ask_question_step(chat_id, 4)
            except:
                bot.send_message(chat_id, "Помилка! Введіть число (грн):")
    # Шаг 4 — зарплата специалиста
    elif step == 4:
        if message.text == "15% від вартості послуги":
            user_data[chat_id]['salary_percent'] = 15
        else:
            try:
                val = float(message.text.replace("%",""))
                user_data[chat_id]['salary_percent'] = val
            except:
                bot.send_message(chat_id, "Помилка! Введіть число %:")
                return

        # Расчет окупаемости
        cost_uah = user_data[chat_id]['cost'] * USD_UAH
        net_profit = (user_data[chat_id]['price'] * user_data[chat_id]['count']) - \
                     (user_data[chat_id]['price'] * user_data[chat_id]['salary_percent']/100 * user_data[chat_id]['count'])
        months = round(cost_uah / net_profit, 1)
        salary_per_procedure = user_data[chat_id]['price'] * user_data[chat_id]['salary_percent']/100

        text = f"""
IPL A-Tone
Вартість апарату: {user_data[chat_id]['cost']}€
Кількість процедур в місяць: {user_data[chat_id]['count']}
Вартість процедури: {user_data[chat_id]['price']} грн
Заробітня плата фахівця за процедуру: {salary_per_procedure} грн
Окупність апарату: {months} місяців

Для звʼязку з менеджером пишіть сюди: @alex_digital_beauty
"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("👨‍💼 Звʼязок з менеджером", "⬅️ Повернутись в меню")
        bot.send_message(chat_id, text, reply_markup=markup)

        # Сбрасываем шаг, но оставляем возможность вернуться в меню
        user_data.pop(chat_id, None)

# Вебхук для Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# Проверка на Render
@app.route("/")
def index():
    return "Бот працює через webhook!", 200

if __name__ == "__main__":
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
