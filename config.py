import os

from dotenv import load_dotenv

load_dotenv()
DB_PASS = os.environ.get('MYSQL_ROOT_PASSWORD')
DB_NAME = os.environ.get('MYSQL_DATABASE')
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
TOKEN_API = os.environ.get('TOKEN_API')
