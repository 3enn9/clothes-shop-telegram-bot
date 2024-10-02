import os

from fastapi import FastAPI
import yookassa
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

TOKEN = str(os.getenv("BOT_TOKEN"))
ID = str(os.getenv("ID"))
ip = os.getenv('IP')
DB_USER = str(os.getenv('DB_USER'))
DB_PASSWORD = str(os.getenv('DB_PASSWORD'))
DB_NAME = str(os.getenv('DB_NAME'))
URL_APP = str(os.getenv('URL_APP'))
DB_URL = os.getenv('DB_URL')
API_KEY = str(os.getenv('API_KEY'))
shopID = str(os.getenv('SHOPID'))
key = str(os.getenv('KEY'))

bot = Bot(token=TOKEN)
app = FastAPI()

yookassa.Configuration.account_id = shopID
yookassa.Configuration.secret_key = key
