import os
import openai
import telebot
import boto3
from boto3.dynamodb.conditions import Key

# Initialize OpenAI API, Telegram Bot, and DynamoDB
openai.api_key = os.environ['OPENAI_API_KEY']
bot = telebot.TeleBot(os.environ['TELEGRAM_BOT_TOKEN'])
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

# Get the question count for the user
def get_question_count(user_id):
    response = table.get_item(Key={'user_id': user_id})
    return response['Item']['question_count'] if 'Item' in response and 'question_count' in response['Item'] else 0

# Update the question count in DynamoDB
def update_question_count(user_id, question_count):
    table.put_item(Item={'user_id': user_id, 'question_count': question_count})

# Handle /start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello! I'm an expert marketing specialist. I'm sassy and a bit funny. Ask me any digital marketing question!")

# Handle text messages
@bot.message_handler(func=lambda message: True)
def ask_question(message):
    user_id = message.chat.id
    question_count = get_question_count(user_id)
    update_question_count(user_id, question_count + 1)

    # Get a response from OpenAI API
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Act as an expert marketing specialist with a savvy but funny tone: {message.text}",
        max_tokens=150,
        n=1,
        temperature=0.8,
    )

    # Send the response to the user
    bot.send_message(user_id, response.choices[0].text.strip())

def lambda_handler(event, context):
    bot.process_new_messages([telebot.types.Update.de_json(event["body"])])

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": "OK",
    }
