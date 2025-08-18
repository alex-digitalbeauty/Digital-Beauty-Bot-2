import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

TOKEN = "8225106462:AAF1lwaxNmFT3H9jtxATDDgF8V-krfUa3zI"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Курс евро
EUR_TO_UAH = 49

# Хранение данных пользователей
user_data = {}

# Главное меню
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Розрахувати окупність апарату", callback_data="calc"))
    markup.add(InlineKeyboardButton("Звʼязок з менеджером", url="https://t.me/alex_digital_beauty"))
    return markup

# Меню выбора аппарата
def aparat_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("IPL A-Tone", callback_data="IPL A-Tone"))
    markup.add(InlineKeyboardButton("Finexel CO2", callback_data="Finexel CO2"))
    markup.add(InlineKeyboardButton("10THERMA", callback_data="10THERMA"))
    return markup

# Меню выбора вариантов
def make_options(question, options):
    markup = InlineKeyboardMarkup()
    for option in options:
        markup.add(InlineKeyboardButton(option, callback_data=option))
    return markup

# Начало
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Виберіть опцію:", reply_markup=main_menu())

# Callback handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    cid = call.message.chat.id
    text = call.data

    # Начало расчета
    if text == "calc":
        user_data[cid] = {}
        bot.send_message(cid, "Оберіть апарат:", reply_markup=aparat_menu())
        return

    # Выбор аппарата
    if text in ["IPL A-Tone", "Finexel CO2", "10THERMA"]:
        user_data[cid]["апарат"] = text
        bot.send_message(cid, "Вартість апарату:", reply_markup=make_options("Вартість", ["27000€", "Інша"]))
        return

    # Вопросы по окупаемости
    if text == "27000€":
        user_data[cid]["вартість"] = 27000
        bot.send_message(cid, "Кількість процедур на місяць:", reply_markup=make_options("К-сть процедур", ["200 процедур", "Інша"]))
        return
    if text == "200 процедур":
        user_data[cid]["procedures"] = 200
        bot.send_message(cid, "Вартість процедури:", reply_markup=make_options("Вартість процедури", ["3500 грн", "Інша"]))
        return
    if text == "3500 грн":
        user_data[cid]["price"] = 3500
        bot.send_message(cid, "Заробітня плата фахівця (%):", reply_markup=make_options("ЗП", ["15%", "Інша"]))
        return
    if text == "15%":
        user_data[cid]["salary_percent"] = 15

        # Расчет окупаемости
        cost_uah = user_data[cid]["вартість"] * EUR_TO_UAH
        profit_per_month = (user_data[cid]["price"] * user_data[cid]["procedures"]) - (user_data[cid]["price"] * user_data[cid]["procedures"] * user_data[cid]["salary_percent"]/100)
        months = round(cost_uah / profit_per_month, 1)
        salary_amount = int(user_data[cid]["price"] * user_data[cid]["salary_percent"]/100)

        result = f"• Вартість апарату: {user_data[cid]['вартість']}€\n" \
                 f"• Кількість процедур в місяць: {user_data[cid]['procedures']}\n" \
                 f"• Вартість процедури: {user_data[cid]['price']} грн\n" \
                 f"• Заробітня плата фахівця за процедуру: {user_data[cid]['salary_percent']}% ({salary_amount} грн)\n" \
                 f"• Окупність апарату: {months} місяців\n\n" \
                 f"Для звʼязку з менеджером пишіть сюди: @alex_digital_beauty"

        bot.send_message(cid, result, reply_markup=main_menu())
        return

    # Здесь можно добавить обработку "Інша" если нужно
    bot.send_message(cid, "Обробка іншої відповіді поки що не реалізована.", reply_markup=main_menu())

# Flask webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running"

# Устанавливаем webhook
@app.before_first_request
def set_webhook():
    url = f"{os.environ.get('RENDER_EXTERNAL_URL')}/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
