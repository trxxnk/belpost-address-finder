import pandas as pd
import numpy as np
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import Session

from db_config import db_config 
from models import Address
from logger import get_configured_logger

# Создание логгера для модуля
logger = get_configured_logger("addr_corr.db.create_streets_book")

def create_streets_book(output_file: str):
    
    logger.info("Подключение к БД...")
    engine = create_engine(db_config.MYSQL_URL)
    session = Session(engine)
    logger.info("Запрос...")
    addresses = session.query(
        Address.id,
        Address.soato_oblast,
        Address.soato_district,
        Address.soato_sovet,
        Address.soato_tip,
        Address.soato_name,
        Address.streetType,
        Address.streetName
    ).order_by().all()
    logger.info("Обработка...")
    # Словарь для замены сокращений
    replace_dict = {
            "г.": "город",
            "аг.": "агрогородок", 
            "гп": "городской поселок",
            "д.": "деревня",
            "с/с": "сельский совет",
            "р-н": "район",
            "п.": "поселок",
            "рп": "рабочий поселок",
            "кп": "курортный поселок",
            "х.": "хутор",
            "пгт": "поселок городского типа",
        }
    df = pd.DataFrame(addresses, columns=["id", "soato_oblast", "soato_district", "soato_sovet", "soato_tip", "soato_name", "streetType", "streetName"])
    logger.info(f"Получено адресов: {len(df)}")
    df = df[~df["streetType"].isna()]
    df = df[~df["streetName"].isna()]
    df["combo_count"] = (
    df.groupby(["soato_name", "streetType", "streetName"])["id"]
    .transform("count"))
    df = df[df["combo_count"] > 10].drop(columns="combo_count")
    df.to_csv("db/from_db_prep.csv", index=False)
    df.sort_values(by=["soato_oblast", "soato_district", "soato_sovet", "soato_name", "streetName"], inplace=True)
    df["soato_tip"] = df["soato_tip"].apply(lambda x: replace_dict[x])
    df["address"] = ""
    df.loc[~df["soato_oblast"].isna(), "address"] += df["soato_oblast"] + " область "
    df.loc[~df["soato_district"].isna(), "address"] += df["soato_district"] + " район "
    df.loc[~df["soato_sovet"].isna(), "address"] += df["soato_sovet"] + " сельсовет "
    df["address"] += df["soato_tip"] + " " + df["soato_name"] + " "
    df.loc[~df["streetType"].isna(), "address"] += df["streetType"] + " " + df["streetName"]
    df["address"] = df["address"].apply(lambda x: x.strip().lower())
    df.drop(columns=["id"], inplace=True)
    df = df.drop_duplicates()
    df["streetName"] = df["streetName"].apply(lambda x: x.lower().capitalize())
    logger.info(f"Всего улиц: {len(df)}")
    logger.info("Запись в файл...")
    df.to_csv(output_file, index=False)
    logger.info(f"Записано {len(df)} улиц в `{output_file}`")
    session.close()

if __name__ == "__main__":
    output_file = "db/addresses_book.csv"
    create_streets_book(output_file)