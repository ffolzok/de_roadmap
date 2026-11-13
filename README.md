# DE Roadmap: ETL Pipeline

Учебный проект по переходу в Data Engineering. Представляет собой ETL-пайплайн для извлечения, трансформации и загрузки данных в базу данных PostgreSQL.

## 🛠 Стек технологий
*   **Язык:** Python 3.15
*   **Обработка данных:** Pandas
*   **База данных:** PostgreSQL 16 (в Docker)
*   **ORM/Драйвер:** SQLAlchemy, psycopg
*   **Инфраструктура:** Docker, Git

## ⚙️ Как это работает
1.  **Extract:** Скрипт обращается к публичному API (`jsonplaceholder`), получает данные и использует библиотеку `tenacity` для повторных попыток в случае сбоя сети.
2.  **Transform:** С помощью Pandas данные очищаются от пустых значений, приводятся к строгим типам (int, str) и обогащаются технической колонкой `load_date`.
3.  **Load:** Очищенные данные загружаются в таблицу `raw_transactions` в PostgreSQL. Используется режим `replace` для обеспечения идемпотентности (защита от дублей).

## 🚀 Как запустить локально
1.  Клонируйте репозиторий.
2.  Запустите базу данных: 
    `docker run --name pg-de -e POSTGRES_PASSWORD=secret -e POSTGRES_USER=de_user -e POSTGRES_DB=de_db -p 5432:5432 -d postgres:16`
3.  Создайте виртуальное окружение и установите зависимости:
    `pip install -r requirements.txt` *(см. примечание ниже)*
4.  Создайте файл `.env` по образцу `.env.example`.
5.  Запустите скрипт:
    `python etl_pipeline.py`