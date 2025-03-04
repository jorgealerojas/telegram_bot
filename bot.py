import os
import openai
import telebot
from telebot import types

# Initialize OpenAI API and Telegram Bot
openai.api_key = os.environ['OPENAI_API_KEY']
bot = telebot.TeleBot(os.environ['TELEGRAM_BOT_TOKEN'])

# Keep track of user's question count
user_question_count = {}

# Handle /start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello! I'm an expert marketing specialist. I'm sassy and a bit funny. Ask me any digital marketing question!")

# Handle text messages
@bot.message_handler(func=lambda message: True)
def ask_question(message):
    user_id = message.chat.id

    # Update the question count
    if user_id not in user_question_count:
        user_question_count[user_id] = 0
    user_question_count[user_id] += 1

    #if user_question_count[user_id] > 3:
        # Request payment after 3 free questions
        #price = types.LabeledPrice("Continue asking questions", 100)  # 100 is the price in the smallest units (1 USD)
        #bot.send_invoice(user_id, "Continue asking questions", "Get unlimited access to marketing advice", "PAYMENT_PAYLOAD", os.environ['PAYMENTS_PROVIDER_TOKEN'], "USD", [price])
    #else:
        # Get a response from GPT-4
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Act as an expert marketing specialist with a savvy but funny tone"},
            {"role": "user", "content": "What's digital marketing?"},
            {"role": "assistant", "content": "Digital marketing is all about leveraging online channels to reach your target audience."}
        ]
    )
    
    # Send the response to the user
    bot.send_message(user_id, response['choices'][0]['message']['content'].strip())


# Handle successful payments
@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    user_id = message.chat.id
    user_question_count[user_id] = 0
    bot.send_message(user_id, "Payment successful! You can now continue asking questions.")

# Run the bot
bot.polling()
