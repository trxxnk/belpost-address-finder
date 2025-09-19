import os
import pandas as pd
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import Session
from tqdm import tqdm
from dotenv import load_dotenv
import time
import gc

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
    print(f"Loading data from {EXCEL_FILE}...")
    
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: File {EXCEL_FILE} not found!")
        return
    
    start_time = time.time()
    
    print("Reading Excel file (this may take a while for large files)...")
    try:
        df = pd.read_excel(
            EXCEL_FILE, 
            engine='openpyxl'
        )
        print(f"Excel file loaded. Found {len(df)} rows.")
        
        total_rows = len(df)
        chunks = [df[i:i + BATCH_SIZE] for i in range(0, total_rows, BATCH_SIZE)]
        print(f"Split into {len(chunks)} chunks of {BATCH_SIZE} rows each.")
        
        del df
        gc.collect()
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    engine = get_database_connection()
    
    total_imported = 0
    
    for chunk_idx, chunk_df in enumerate(chunks):
        chunk_start_time = time.time()
        print(f"Processing chunk {chunk_idx+1}/{len(chunks)}...")
        
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
            print(f"Imported {len(addresses)} addresses in this batch. Total: {total_imported}")
            print(f"Chunk processing time: {chunk_time:.2f} seconds ({len(addresses)/chunk_time:.2f} rows/sec)")
            
            del addresses
            del chunk_df
            gc.collect()
            
        except Exception as e:
            print(f"Error importing batch: {e}")
    
    total_time = time.time() - start_time
    print(f"Import completed. Total addresses imported: {total_imported}")
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Average import speed: {total_imported/total_time:.2f} rows/sec")

if __name__ == "__main__":
    import_addresses_from_excel()
