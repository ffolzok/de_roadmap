import os
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_currency_data():
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    logger.info(f"Запрос к ЦБ: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # ВАЖНО: Возвращаем content (байты), чтобы BeautifulSoup сам определил кодировку из XML
        return response.content
    except Exception as e:
        logger.error(f"Ошибка при запросе: {e}")
        return None

def parse_currency_data(xml_content):
    if not xml_content:
        return None
        
    logger.info("Парсинг XML...")
    soup = BeautifulSoup(xml_content, 'xml')
    
    result = []
    
    for code in ['USD', 'EUR']:
        valute = None
        # Ищем нужную валюту перебором, так как CharCode - это тег, а не атрибут
        for v in soup.find_all('Valute'):
            if v.find('CharCode').text.strip() == code:
                valute = v
                break
                
        if valute:
            name = valute.find('Name').text.strip()
            nominal = int(valute.find('Nominal').text.strip())
            value_str = valute.find('Value').text.strip()
            
            # Очистка данных: меняем запятую на точку и считаем курс за 1 единицу
            value = float(value_str.replace(',', '.'))
            rate_per_unit = value / nominal
            
            result.append({
                'currency_code': code,        # Переименовали в currency_code для БД
                'name': name,
                'nominal': nominal,
                'rate': value,                # Официальный курс ЦБ
                'rate_per_unit': round(rate_per_unit, 4),
                'source': 'CBR'
            })
            
    return result

def load_to_db(currencies):
    if not currencies:
        logger.warning("Нет данных для загрузки в БД.")
        return

    logger.info("Загрузка данных в PostgreSQL...")
    load_dotenv()
    
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    try:
        engine = create_engine(db_url)
        df = pd.DataFrame(currencies)
        
        # Добавляем техническую колонку
        df['load_date'] = pd.Timestamp.now()
        
        # Принудительно приводим типы, чтобы SQLAlchemy создала правильные колонки
        df['nominal'] = df['nominal'].astype(int)
        df['rate'] = df['rate'].astype(float)
        df['rate_per_unit'] = df['rate_per_unit'].astype(float)
        
        # Записываем в базу
        df.to_sql('currency_rates', con=engine, if_exists='replace', index=False)
        
        logger.info(f"Успешно загружено {len(df)} строк в таблицу currency_rates.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке в БД: {e}")

if __name__ == "__main__":
    logger.info("=== Старт парсера ЦБ ===")
    
    xml_data = fetch_currency_data()
    currencies = parse_currency_data(xml_data)
    
    if currencies:
        for curr in currencies:
            logger.info(f"Валюта: {curr['currency_code']} ({curr['name']})")
            logger.info(f"  Номинал: {curr['nominal']}")
            logger.info(f"  Курс: {curr['rate']}")
            logger.info(f"  За 1 единицу: {curr['rate_per_unit']} руб.")
            logger.info("-" * 30)
            
        # Загружаем в БД
        load_to_db(currencies)
    else:
        logger.error("Не удалось получить данные.")
        
    logger.info("=== Финиш парсера ЦБ ===")