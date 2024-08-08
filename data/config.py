import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = str(os.getenv("BOT_TOKEN"))
ID = str(os.getenv("ID"))
ip = os.getenv('IP')
DB_USER = str(os.getenv('DB_USER'))
DB_PASSWORD = str(os.getenv('DB_PASSWORD'))
DB_NAME = str(os.getenv('DB_NAME'))
DB_URL_LITE = os.getenv('DB_URL_LITE')
DB_URL = os.getenv('DB_URL')

