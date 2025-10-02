"""
Настройки для postal_service
"""

import os
from dotenv import load_dotenv

load_dotenv()

class PostalConfig:
    """Настройки данных"""
    def __init__(self):
        self.postal_host = os.getenv("POSTAL_SERVICE_HOST")
        self.postal_port = os.getenv("POSTAL_SERVICE_PORT")
        self.postal_url = f"http://{self.postal_host}:{self.postal_port}"
        
        
postal_config = PostalConfig()