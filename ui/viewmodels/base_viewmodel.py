"""
Базовый класс ViewModel для приложения.
Реализует паттерн Observer для уведомления UI об изменениях.
"""

from typing import Dict, Any, Callable, List
from logger import get_configured_logger

logger = get_configured_logger("ui.viewmodels.base_viewmodel")


class BaseViewModel:
    """
    Базовый класс для всех ViewModel.
    Реализует паттерн Observer для уведомления UI об изменениях.
    """
    
    def __init__(self):
        self._callbacks: Dict[str, List[Callable]] = {}
        
    def register_callback(self, property_name: str, callback: Callable) -> None:
        """
        Регистрация колбэка для оповещения об изменении свойства
        
        Args:
            property_name: Имя свойства, за изменением которого следить
            callback: Функция обратного вызова
        """
        if property_name not in self._callbacks:
            self._callbacks[property_name] = []
        self._callbacks[property_name].append(callback)
        
    def notify(self, property_name: str) -> None:
        """
        Оповещение об изменении свойства
        
        Args:
            property_name: Имя изменившегося свойства
        """
        if property_name in self._callbacks:
            for callback in self._callbacks[property_name]:
                try:
                    callback()
                except Exception as e:
                    # Логирование ошибки в колбэке, но не прерывание выполнения
                    logger.error(f"Ошибка в колбэке для свойства '{property_name}': {e}")
    
    def unregister_callback(self, property_name: str, callback: Callable) -> None:
        """
        Отмена регистрации колбэка
        
        Args:
            property_name: Имя свойства
            callback: Функция обратного вызова для удаления
        """
        if property_name in self._callbacks:
            try:
                self._callbacks[property_name].remove(callback)
            except ValueError:
                # Колбэк не найден, игнорируем
                pass
    
    def unregister_all_callbacks(self, property_name: str) -> None:
        """
        Отмена регистрации всех колбэков для свойства
        
        Args:
            property_name: Имя свойства
        """
        if property_name in self._callbacks:
            self._callbacks[property_name].clear()
    
    def clear_all_callbacks(self) -> None:
        """
        Очистка всех зарегистрированных колбэков
        """
        self._callbacks.clear()
