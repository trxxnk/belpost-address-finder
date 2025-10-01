import os
import pandas as pd
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import Session
from tqdm import tqdm
from dotenv import load_dotenv
import time
import gc
import re

from models import Base, Address

load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DB")

EXCEL_FILE = os.path.join("private_data", "КО_адреса.xlsx")

BATCH_SIZE = 20000

def get_database_connection():
    url = URL.create(
        drivername="mysql+mysqlconnector",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DB,
    )
    engine = create_engine(url, echo=False)
    return engine

def _safe_convert_to_int(value):
    if pd.isna(value) or value is None:
        return None
        
    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            value = value.replace(',', '.')
        
        return int(float(value))
    except (ValueError, TypeError):
        return None

def import_addresses_from_excel():
    # print(f"Loading data from {EXCEL_FILE}...")
    
    if not os.path.exists(EXCEL_FILE):
        # print(f"Error: File {EXCEL_FILE} not found!")
        return
    
    start_time = time.time()
    
    # print("Reading Excel file (this may take a while for large files)...")
    try:
        df = pd.read_excel(
            EXCEL_FILE, 
            engine='openpyxl'
        )
        # print(f"Excel file loaded. Found {len(df)} rows.")
        
        total_rows = len(df)
        chunks = [df[i:i + BATCH_SIZE] for i in range(0, total_rows, BATCH_SIZE)]
        # print(f"Split into {len(chunks)} chunks of {BATCH_SIZE} rows each.")
        
        del df
        gc.collect()
        
    except Exception as e:
        # print(f"Error reading Excel file: {e}")
        return
    
    engine = get_database_connection()
    
    total_imported = 0
    
    for chunk_idx, chunk_df in enumerate(chunks):
        chunk_start_time = time.time()
        # print(f"Processing chunk {chunk_idx+1}/{len(chunks)}...")
        
        chunk_df.columns = [col.strip() if isinstance(col, str) else col for col in chunk_df.columns]
        
        addresses = []
        
        for idx, row in tqdm(chunk_df.iterrows(), total=len(chunk_df), desc="Creating address objects"):
            street_val, building_val, imns_val, oblast_val, \
            district_val, sovet_val, tip_val, name_val = row.values
            
            address = Address(
                id=idx,
                street=str(street_val) if pd.notna(street_val) else None,
                building=str(building_val) if pd.notna(building_val) else None,
                soato_imns=_safe_convert_to_int(imns_val),
                soato_oblast=str(oblast_val) if pd.notna(oblast_val) else None,
                soato_district=str(district_val) if pd.notna(district_val) else None,
                soato_sovet=str(sovet_val) if pd.notna(sovet_val) else None,
                soato_tip=str(tip_val) if pd.notna(tip_val) else None,
                soato_name=str(name_val) if pd.notna(name_val) else None
            )
            addresses.append(address)
        
        try:
            with Session(engine) as session:
                session.add_all(addresses)
                session.commit()
                
            total_imported += len(addresses)
            chunk_time = time.time() - chunk_start_time
            # print(f"Imported {len(addresses)} addresses in this batch. Total: {total_imported}")
            # print(f"Chunk processing time: {chunk_time:.2f} seconds ({len(addresses)/chunk_time:.2f} rows/sec)")
            
            del addresses
            del chunk_df
            gc.collect()
            
        except Exception as e:
            # print(f"Error importing batch: {e}")
    
    total_time = time.time() - start_time
    # print(f"Import completed. Total addresses imported: {total_imported}")
    # print(f"Total execution time: {total_time:.2f} seconds")
    # print(f"Average import speed: {total_imported/total_time:.2f} rows/sec")

def grouped_to_dict(grouped_abbrs: dict[str:list[str]]) -> dict[str:str]:
    abbrs_dict = dict()
    for fullname, abbrs in grouped_abbrs.items():
        for abbr in abbrs:
            abbrs_dict[abbr] = fullname
    return abbrs_dict

def fill_street_type_and_name_orm(session: Session, abbr_dict: dict):
    """
    Для всех Address обновляет поля streetType и streetName на основе справочника аббревиатур.
    abbr_dict: dict, где ключ — аббревиатура, значение — расшифровка.
    """
    abbrs = sorted(abbr_dict.keys(), key=len, reverse=True)
    abbr_pattern = r'^(' + '|'.join([re.escape(a) for a in abbrs]) + r')\s*'
    abbr_re = re.compile(abbr_pattern, flags=re.IGNORECASE)

    def extract_type_and_street(text):
        if not isinstance(text, str):
            return (None, text)
        m = abbr_re.match(text)
        if m:
            abbr = m.group(1)
            street_type = abbr_dict.get(abbr, abbr_dict.get(abbr.upper(), None))
            street_name = text[m.end():].strip()
            return (street_type, street_name)
        else:
            return (None, text.strip() if isinstance(text, str) else text)

    addresses = session.query(Address).all()
    from tqdm import tqdm
    for i, addr in enumerate(tqdm(addresses, desc="Updating streetType/streetName")):
        street = addr.street
        street_type, street_name = extract_type_and_street(street)
        addr.streetType = street_type
        addr.streetName = street_name
        if i % 10_000 == 0:
            session.commit()
            gc.collect()
    session.commit()

if __name__ == "__main__":
    import_addresses_from_excel()
