import os
import logging
import requests
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 1. Загружаем переменные из .env
load_dotenv()

# 2. Настраиваем логирование (пишем и в файл, и в консоль)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract():
    url = os.getenv("API_URL")
    logger.info(f"Extract: запрос к {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Extract: успешно получено {len(data)} записей.")
        return data
    except Exception as e:
        logger.error(f"Extract: ошибка - {e}")
        return None

def transform(data):
    if not data:
        return None
    logger.info("Transform: начало обработки данных.")
    df = pd.DataFrame(data)
    
    # --- TODO 1: Сделайте трансформации ---
    # 1. Оставьте только колонки: 'userId', 'id', 'title' (df = df[['userId', 'id', 'title']])
    # 2. Переименуйте 'userId' в 'user_id', а 'title' в 'transaction_title' (используйте df.rename(columns={...}, inplace=True))
    # 3. Добавьте колонку 'load_date' с текущим временем (df['load_date'] = datetime.now())
    # 4. Удалите строки, где 'transaction_title' пустой (df.dropna(subset=['transaction_title'], inplace=True))
    
    # Напишите ваш код здесь:
    # 1. Оставляем только нужные колонки
    df = df[['userId', 'id', 'title']]

    # 2. Переименовываем колонки
    df = df.rename(columns={'userId': 'user_id', 'title': 'transaction_title'})

    # 3. Добавляем колонку с текущей датой и временем
    df['load_date'] = datetime.now()

    # 4. Удаляем пустые заголовки (если они есть)
    df = df.dropna(subset=['transaction_title'])

    
    logger.info(f"Transform: готово. Строк: {len(df)}")
    return df

def load(df):
    if df is None or df.empty:
        logger.warning("Load: нет данных для загрузки.")
        return
    
    logger.info("Load: начало загрузки в БД.")
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    try:
        engine = create_engine(db_url)
        
        # --- TODO 2: Загрузите данные в таблицу ---
        # Используйте метод df.to_sql()
        # Название таблицы: 'raw_transactions'
        # Параметры: if_exists='append', index=False
        # Подключение: con=engine
        
        # Напишите ваш код здесь:
        df.to_sql('raw_transactions', con=engine, if_exists='replace', index=False)
        
        logger.info(f"Load: успешно загружено {len(df)} строк.")
    except Exception as e:
        logger.error(f"Load: ошибка при загрузке - {e}")

if __name__ == "__main__":
    logger.info("=== Старт ETL ===")
    raw = extract()
    clean = transform(raw)
    load(clean)
    logger.info("=== Финиш ETL ===")