import os
import openai
import telebot
import boto3
from boto3.dynamodb.conditions import Key
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize OpenAI API, Telegram Bot, and DynamoDB
openai.api_key = os.environ['OPENAI_API_KEY']
bot = telebot.TeleBot(os.environ['TELEGRAM_BOT_TOKEN'])
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

# Get the user data
def get_user_data(user_id):
    response = table.get_item(Key={'user_id': user_id})
    return response['Item'] if 'Item' in response else None

# Update the question count and paid status in DynamoDB
def update_user_data(user_id, username, question_count, has_paid):
    table.put_item(Item={'user_id': str(user_id), 'username': str(username), 'question_count': question_count, 'has_paid': has_paid})

# Check if the user has paid
def has_user_paid(user_id):
    user_data = get_user_data(user_id)
    return user_data['has_paid'] if user_data and 'has_paid' in user_data else False

# Handle text messages
def ask_question(message):
    user_id = message.chat.id
    username = message.chat.username
    user_data = get_user_data(str(user_id))
    
    #logging.info(f"ask_question called for user {user_id}")

    if not user_data:
        question_count = 0
        has_paid = False
    else:
        question_count = user_data['question_count']
        has_paid = user_data['has_paid']

    if question_count >= 5 and not has_paid:
        bot.send_message(user_id, "Haz alcanzado 5 preguntras gratis. Para continuar disfrutando de marketero, contacta al administrador para hacer tu donación: @Carlosdaniel")
        return

    question_count += 1
    update_user_data(str(user_id), username, question_count, has_paid)

    # Get a response from OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", #"gpt-4",
        messages=[
            {"role": "system", "content": "Actua como un experto especialista en marketing digital, con un tono inteligente pero divertido. Responde de forma muy precisa, sin dejar de lado tu tono."},
            {"role": "user", "content": message.text},
        ]
    )

    # Send the response to the user
    bot.send_message(user_id, response['choices'][0]['message']['content'].strip())


def lambda_handler(event, context):
    #logger.info(f"Event: {event}")
    update = telebot.types.Update.de_json(event["body"])
    message = update.message or update.edited_message  # This line handles both regular messages and edited messages
    #logger.info(f"Message: {message}")
    
    if message:
        ask_question(message)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": "OK",
    }