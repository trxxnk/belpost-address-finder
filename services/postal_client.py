import requests
from typing import Dict, Any, Optional
import json
import urllib.parse

class PostalClient:
    """Клиент для взаимодействия с микросервисом парсинга адресов"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Инициализация клиента
        
        Args:
            base_url: Базовый URL микросервиса
        """
        self.base_url = base_url
    
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
            print(f"[DEBUG] Исходный адрес: '{address}'")
            
            # Кодируем адрес для URL
            encoded_address = urllib.parse.quote(address)
            
            # Используем GET-запрос с параметрами
            url = f"{self.base_url}/parse"
            
            # Создаем полный URL с параметрами для отладки
            full_url = f"{url}?address={encoded_address}"
            print(f"[DEBUG] Полный URL: {full_url}")
            
            # Отправляем запрос
            print(f"[REQUEST] GET {url} с параметром address={encoded_address}")
            
            response = requests.get(
                url,
                params={"address": address},
                timeout=10  # Увеличиваем таймаут до 10 секунд
            )
            
            print(f"[RESPONSE] Статус: {response.status_code}")
            print(f"[RESPONSE] Заголовки: {dict(response.headers)}")
            print(f"[RESPONSE] Кодировка: {response.encoding}")
            
            if response.status_code == 200:
                try:
                    # Пробуем декодировать JSON
                    response_data = response.json()
                    print(f"[RESPONSE] Данные JSON: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    
                    # Проверяем, не пустой ли словарь
                    if not response_data:
                        print("[WARNING] Получен пустой словарь данных")
                    
                    return response_data
                except json.JSONDecodeError as json_err:
                    print(f"[ERROR] Ошибка декодирования JSON: {json_err}")
                    print(f"[ERROR] Полученный текст: {response.text}")
                    return {}
            else:
                print(f"[ERROR] Ошибка при парсинге адреса: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            print(f"[ERROR] Ошибка при отправке запроса: {str(e)}")
            return {}
    
    def check_health(self) -> bool:
        """
        Проверяет работоспособность микросервиса
        
        Returns:
            bool: True если сервис доступен, иначе False
        """
        try:
            url = f"{self.base_url}/health"
            print(f"[REQUEST] GET {url}")
            
            response = requests.get(url, timeout=5)
            
            print(f"[RESPONSE] Статус: {response.status_code}")
            print(f"[RESPONSE] Сырой текст: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[RESPONSE] Данные: {data}")
                    return True
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Ошибка декодирования JSON: {e}")
                    return False
            
            return False
        except Exception as e:
            print(f"[ERROR] Ошибка при проверке доступности сервиса: {str(e)}")
            return False