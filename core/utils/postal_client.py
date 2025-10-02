import requests
from typing import Dict, Any, Optional
import json
import urllib.parse
from logger import get_configured_logger

logger = get_configured_logger("core.utils.postal_client")

class PostalClient:
    """Клиент для взаимодействия с микросервисом парсинга адресов"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        logger.info(f"Инициализирован PostalClient с базовым URL: {base_url}")
    
    def parse_address(self, address: str) -> Dict[str, Any]:
        """
        Отправляет запрос на парсинг адреса
        
        Args:
            address: Строка с адресом для парсинга
            
        Returns:
            Dict[str, Any]: Структурированный адрес или пустой словарь в случае ошибки
        """
        try:
            # Выводим адрес для отладки
            logger.debug(f"Исходный адрес: '{address}'")
            
            # Кодируем адрес для URL
            encoded_address = urllib.parse.quote(address)
            
            # Используем GET-запрос с параметрами
            url = f"{self.base_url}/parse"
            
            # Создаем полный URL с параметрами для отладки
            full_url = f"{url}?address={encoded_address}"
            logger.debug(f"Полный URL: {full_url}")
            
            # Отправляем запрос
            logger.debug(f"GET {url} с параметром address={encoded_address}")
            
            response = requests.get(
                url,
                params={"address": address},
                timeout=10  # Увеличиваем таймаут до 10 секунд
            )
            
            logger.debug(f"Статус: {response.status_code}")
            logger.debug(f"Заголовки: {dict(response.headers)}")
            logger.debug(f"Кодировка: {response.encoding}")
            
            if response.status_code == 200:
                try:
                    # Пробуем декодировать JSON
                    response_data = response.json()
                    logger.debug(f"Данные JSON: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    
                    # Проверяем, не пустой ли словарь
                    if not response_data:
                        logger.warning("Получен пустой словарь данных")
                    
                    return response_data
                except json.JSONDecodeError as json_err:
                    logger.error(f"Ошибка декодирования JSON: {json_err}")
                    logger.error(f"Полученный текст: {response.text}")
                    return {}
            else:
                logger.error(f"Ошибка при парсинге адреса: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Ошибка при отправке запроса: {str(e)}")
            return {}
    
    def check_health(self) -> bool:
        """
        Проверяет работоспособность микросервиса
        
        Returns:
            bool: True если сервис доступен, иначе False
        """
        try:
            url = f"{self.base_url}/health"
            logger.debug(f"GET {url}")
            
            response = requests.get(url, timeout=5)
            
            logger.debug(f"Статус: {response.status_code}")
            logger.debug(f"Сырой текст: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Данные: {data}")
                    return True
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка декодирования JSON: {e}")
                    return False
            
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке доступности сервиса: {str(e)}")
            return False