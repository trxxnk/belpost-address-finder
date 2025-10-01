"""
Модуль с иерархией исключений для приложения.
Содержит базовые и специализированные классы исключений,
которые используются во всех модулях приложения для
более точной обработки ошибок.
"""


class AppBaseException(Exception):
    """Базовое исключение приложения"""
    def __init__(self, message="Произошла ошибка в приложении", *args, **kwargs):
        self.message = message
        super().__init__(self.message, *args, **kwargs)


class NetworkException(AppBaseException):
    """Исключение при сетевых ошибках"""
    def __init__(self, message="Ошибка сети", url=None, status_code=None, *args, **kwargs):
        self.url = url
        self.status_code = status_code
        if url and status_code:
            message = f"{message}: URL={url}, код={status_code}"
        elif url:
            message = f"{message}: URL={url}"
        super().__init__(message, *args, **kwargs)


class ParsingException(AppBaseException):
    """Исключение при ошибках парсинга"""
    def __init__(self, message="Ошибка при парсинге данных", source=None, *args, **kwargs):
        self.source = source
        if source:
            message = f"{message} из {source}"
        super().__init__(message, *args, **kwargs)


class DatabaseException(AppBaseException):
    """Исключение при ошибках базы данных"""
    def __init__(self, message="Ошибка базы данных", query=None, *args, **kwargs):
        self.query = query
        if query:
            message = f"{message}: {query}"
        super().__init__(message, *args, **kwargs)


class ConfigurationException(AppBaseException):
    """Исключение при ошибках конфигурации"""
    def __init__(self, message="Ошибка конфигурации", param=None, *args, **kwargs):
        self.param = param
        if param:
            message = f"{message}: параметр '{param}' не настроен или имеет неверное значение"
        super().__init__(message, *args, **kwargs)


class ValidationException(AppBaseException):
    """Исключение при ошибках валидации данных"""
    def __init__(self, message="Ошибка валидации данных", field=None, value=None, *args, **kwargs):
        self.field = field
        self.value = value
        if field and value:
            message = f"{message}: поле '{field}' имеет недопустимое значение '{value}'"
        elif field:
            message = f"{message}: поле '{field}' содержит недопустимое значение"
        super().__init__(message, *args, **kwargs)


class WebDriverException(AppBaseException):
    """Исключение при ошибках работы с веб-драйвером"""
    def __init__(self, message="Ошибка веб-драйвера", driver_info=None, *args, **kwargs):
        self.driver_info = driver_info
        if driver_info:
            message = f"{message}: {driver_info}"
        super().__init__(message, *args, **kwargs)


class ResourceNotFoundException(AppBaseException):
    """Исключение при отсутствии ресурса"""
    def __init__(self, message="Ресурс не найден", resource_type=None, resource_id=None, *args, **kwargs):
        self.resource_type = resource_type
        self.resource_id = resource_id
        if resource_type and resource_id:
            message = f"{message}: {resource_type} с идентификатором '{resource_id}'"
        super().__init__(message, *args, **kwargs)


class BelpostServiceException(AppBaseException):
    """Исключение при ошибках сервиса Белпочты"""
    def __init__(self, message="Ошибка сервиса Белпочты", details=None, *args, **kwargs):
        self.details = details
        if details:
            message = f"{message}: {details}"
        super().__init__(message, *args, **kwargs)
