# telegram_bot

Primero, para crear el bot debes interactuar con el @BotFather para crear tu bot y obtener el API de telegram.

Una vez tengas el API, usando postman debes inicializar el webhook del bot: https://api.telegram.org/bot{TELEGRAM_API_KEY}/setWebhook

Deberías obtener una respuesta como esta:

{
    "ok": true,
    "result": true,
    "description": "Webhook was set"
}

Una vez inicializado, se debe subir el código a un proveedor cloud, en mi caso use AWS: Lambda, API Gateway y DynamoDB