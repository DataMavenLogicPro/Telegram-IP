import telebot
import requests
from bs4 import BeautifulSoup
import schedule
import time
from threading import Thread
import os

# Ваш токен от BotFather
API_TOKEN = os.getenv('API_TOKEN')

# Инициализируем бота
bot = telebot.TeleBot(API_TOKEN)

# URL-ы для проверки
URLS = [
    "https://www.mvideo.ru/products/stilus-dlya-plansheta-xiaomi-redmi-pad-pro-smart-pen-400336407",
    "https://www.eldorado.ru/cat/detail/stilus-xiaomi-redmi-pad-pro-smart-pen-white/?utm_source=google&utm_medium=organic&utm_campaign=google&utm_referrer=google",
    "https://shop.mts.ru/product/stilus-xiaomi-redmi-pad-pro-smart-pen-belyj-bhr8577gl/specs",
    "https://www.dns-shop.ru/product/b92d05072c3bd9cb/stilus-xiaomi-redmi-smart-pen-dla-xiaomi-redmi-pad-pro-pad-pro-5g-belyj/?utm_medium=organic&utm_source=google&utm_referrer=https%3A%2F%2Fwww.google.com%2F",
    "https://www.wildberries.ru/catalog/244492537/detail.aspx"
]

# Сообщение, которое будет отправляться, если товар в наличии
IN_STOCK_MESSAGE = "Товар в наличии! Ссылка: {}"
OUT_OF_STOCK_MESSAGE = "Товара пока нет в наличии."

# Список чатов, которым нужно отправлять уведомления
subscribed_chats = set()

def check_availability():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    available_urls = []
    
    for url in URLS:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if "mvideo" in url:
            availability = soup.find('div', {'class': 'product-details__unavailable'})
            if not availability:
                available_urls.append(url)
        elif "eldorado" in url:
            availability = soup.find('div', {'class': 'j-buy-product-btn j-wba-header-buy-btn'})
            if availability and "data-showroom-quantity" in availability.attrs:
                available_urls.append(url)
        elif "shop.mts" in url:
            availability = soup.find('div', {'class': 'out-of-stock'})
            if not availability:
                available_urls.append(url)
        elif "dns-shop" in url:
            availability = soup.find('div', {'class': 'product-buy__price-block'})
            if availability:
                available_urls.append(url)
        elif "wildberries" in url:
            availability = soup.find('div', {'class': 'sold-out'})
            if not availability:
                available_urls.append(url)
    
    return available_urls

def notify_users():
    available_urls = check_availability()
    for chat_id in subscribed_chats:
        if available_urls:
            for url in available_urls:
                bot.send_message(chat_id, IN_STOCK_MESSAGE.format(url))
        else:
            bot.send_message(chat_id, OUT_OF_STOCK_MESSAGE)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    subscribed_chats.add(chat_id)
    bot.reply_to(message, "Привет! Я бот для проверки наличия товара. Вы автоматически подписаны на уведомления о наличии товара. Используйте /check, чтобы проверить наличие товара вручную.")

@bot.message_handler(commands=['check'])
def check_product(message):
    available_urls = check_availability()
    if available_urls:
        for url in available_urls:
            bot.send_message(message.chat.id, IN_STOCK_MESSAGE.format(url))
    else:
        bot.send_message(message.chat.id, OUT_OF_STOCK_MESSAGE)

def schedule_checks():
    schedule.every(30).minutes.do(notify_users)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Запуск планировщика в отдельном потоке
thread = Thread(target=schedule_checks)
thread.start()

# Запуск бота
bot.polling(none_stop=True)