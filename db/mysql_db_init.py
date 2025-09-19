from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

import os
from dotenv import load_dotenv

from models import Base

load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DB")


def init_database():
    # Подключение к серверу MySQL без указания базы
    url_without_db = URL.create(
        drivername="mysql+mysqlconnector",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
    )
    engine = create_engine(url_without_db, echo=True)

    # Проверяем, есть ли база
    with Session(engine) as session:
        result = session.execute(
            text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :dbname"),
            {"dbname": MYSQL_DB},
        ).fetchone()

        if not result:
            session.execute(text(f"CREATE DATABASE {MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            session.commit()
            print(f"✅ База {MYSQL_DB} создана")
        else:
            print(f"ℹ️ База {MYSQL_DB} уже существует")

    # Подключаемся к базе и создаем таблицы
    url_with_db = URL.create(
        drivername="mysql+mysqlconnector",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DB,
    )
    engine_with_db = create_engine(url_with_db, echo=True)

    Base.metadata.create_all(engine_with_db)
    print("✅ Таблицы созданы / проверены")


if __name__ == "__main__":
    init_database()
