# telegram_bot

First, to create the bot you must interact with the @BotFather to create yours and get the telegram API.

Once you have the API, using postman you must initialize the bot's webhook: https://api.telegram.org/bot{TELEGRAM_API_KEY}/setWebhook

You should get a response like this:

{
     "ok": true,
     "result": true,
     "description": "Webhook was set"
}

Once initialized, the code must be uploaded to a cloud provider, in my case I used AWS: Lambda, API Gateway and DynamoDB
