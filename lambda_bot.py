import os
import openai
import telebot
import boto3
from boto3.dynamodb.conditions import Key
import logging
import threading

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize OpenAI API, Telegram Bot, and DynamoDB
openai.api_key = os.environ['OPENAI_API_KEY']
bot = telebot.TeleBot(os.environ['TELEGRAM_BOT_TOKEN'])
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

# In-memory conversation storage
conversations = {}

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

# Check if more that 10 seconds has pass by since the first "iddle waiting" message  
def send_second_message(user_id, sent_messages, response_received_event):
    response_received_event.wait(10)  # Wait for 10 seconds
    if not response_received_event.is_set():
        sent_messages.append(bot.send_message(user_id, "Relax, ya viene la respuesta..."))

# Handle text messages
def ask_question(message):
    user_id = message.chat.id
    username = message.chat.username
    user_data = get_user_data(str(user_id))

    # Check if message.text is None or an empty string
    if not message.text:
        bot.send_message(user_id, "Oops que pena, podrías enviarme de nuevo tu pregunta? Por ahora sólo puedo procesar texto.")
        return
    
    #logging.info(f"ask_question called for user {user_id}")

    if not user_data:
        question_count = 0
        has_paid = False
    else:
        question_count = user_data['question_count']
        has_paid = user_data['has_paid']

    if question_count >= 5 and not has_paid:
        bot.send_message(user_id, "Haz alcanzado 5 preguntras gratis. Para continuar disfrutando de marketero, contacta al administrador para hacer tu donación: @Botaibyjd")
        return

    question_count += 1
    update_user_data(str(user_id), username, question_count, has_paid)
    
    if user_id not in conversations:
        conversations[user_id] = [
            {"role": "system", "content": """Actúa como un experto especialista en marketing digital llamado Marketero. Eres un profesional con amplia experiencia en:
- Marketing Digital y Estrategia
- SEO y SEM
- Social Media Marketing
- Email Marketing
- Content Marketing
- Analytics y KPIs

Tu tono es profesional pero cercano y divertido. Mantienes un balance perfecto entre ser informativo y entretenido.
Tus respuestas son concisas pero completas, evitando ser demasiado técnico cuando no es necesario.
Siempre das ejemplos prácticos y aplicables."""},
        ]

    # Keep only last 10 messages to manage context window
    if len(conversations[user_id]) > 11:  # 1 system message + 10 conversation messages
        conversations[user_id] = [conversations[user_id][0]] + conversations[user_id][-10:]

    conversations[user_id].append({"role": "user", "content": message.text})
    
    # Send a message with "Preparando respuesta..." to the user
    sent_messages = [bot.send_message(user_id, "Preparando respuesta...")]
    
    # Create an event to signal when the response is received
    response_received_event = threading.Event()
    
    # Start a separate thread to send the second message if needed
    second_message_thread = threading.Thread(target=send_second_message, args=(user_id, sent_messages, response_received_event))
    second_message_thread.start()

    try:
        # Get a response from OpenAI API with GPT-4 Turbo
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=conversations[user_id],
            temperature=0.7,  # Balance between creativity and precision
            max_tokens=600,   # Increased token limit for more detailed responses
            presence_penalty=0.6,  # Encourage diverse responses
            frequency_penalty=0.3   # Reduce repetition
        )
        
        # Signal that the response has been received
        response_received_event.set()
        
        # Wait for the second_message_thread to finish
        second_message_thread.join()
        
        # Delete the "Preparando respuesta..." message and the second message if it was sent
        for message_to_delete in sent_messages:
            bot.delete_message(user_id, message_to_delete.message_id)

        assistant_response = response['choices'][0]['message']['content'].strip()
        
        # Send the response to the user
        bot.send_message(user_id, assistant_response)
        
        # Add the assistant's response to the conversation
        conversations[user_id].append({"role": "assistant", "content": assistant_response})
        
    except Exception as e:
        response_received_event.set()
        second_message_thread.join()
        
        # Delete the "Preparando respuesta..." message and the second message if it was sent
        for message_to_delete in sent_messages:
            try:
                bot.delete_message(user_id, message_to_delete.message_id)
            except:
                pass
                
        error_message = "Lo siento, estoy teniendo problemas para procesar tu pregunta. Por favor, inténtalo de nuevo en un momento."
        bot.send_message(user_id, error_message)
        logger.error(f"Error processing message for user {user_id}: {str(e)}")


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