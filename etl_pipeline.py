import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from requests.exceptions import RequestException
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

@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def extract():
    url = os.getenv("API_URL")
    logger.info(f"Extract: запрос к {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        data = response.json()
        logger.info(f"Extract: успешно получено {len(data)} записей.")
        return data
    except RequestException as e:
        logger.warning(f"Extract: ошибка сети {e}. Пробуем еще раз...")
        raise e # Выбрасываем ошибку наверх, чтобы tenacity понял, что нужно повторить

def transform(data):
    if not data:
        return None
    logger.info("Transform: начало обработки данных.")
    df = pd.DataFrame(data)
        
    # 1. Оставляем только нужные колонки
    df = df[['userId', 'id', 'title']]

    # 2. Переименовываем колонки
    df = df.rename(columns={'userId': 'user_id', 'title': 'transaction_title'})

    # 3. Добавляем колонку с текущей датой и временем
    df['load_date'] = datetime.now()

    # 4. Удаляем пустые заголовки (если они есть)
    df = df.dropna(subset=['transaction_title'])
    # Удаляем строки, где user_id не является числом (грязные данные)
    df = df[pd.to_numeric(df['user_id'], errors='coerce').notna()]
    
    # Приводим типы данных к строгим форматам для базы
    df['user_id'] = df['user_id'].astype(int)
    df['id'] = df['id'].astype(int)
    df['transaction_title'] = df['transaction_title'].astype(str)
    
    logger.info(f"Transform: данные очищены. Строк после валидации: {len(df)}")

    
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