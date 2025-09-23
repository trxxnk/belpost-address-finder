import enum

# Перечисление для областей Беларуси (отсортировано)
class RegionType(enum.Enum):
    NONE = "НЕТ"
    BREST = "БРЕСТСКАЯ"
    VITEBSK = "ВИТЕБСКАЯ"
    GOMEL = "ГОМЕЛЬСКАЯ"
    GRODNO = "ГРОДНЕНСКАЯ"
    MINSK = "МИНСКАЯ"
    MOGILEV = "МОГИЛЕВСКАЯ"

# Перечисления для типов улиц (отсортировано)
class StreetType(enum.Enum):
    NONE = "НЕТ"
    OTHER = "ДРУГОЕ"
    STREET = "УЛИЦА"
    AVENUE = "ПРОСПЕКТ"
    BOULEVARD = "БУЛЬВАР"
    DEAD_END = "ТУПИК"
    DESCENT = "СПУСК"
    DRIVE = "ПРОЕЗД"
    EMBANKMENT = "НАБЕРЕЖНАЯ"
    ENTRANCE = "ВЪЕЗД"
    HIGHWAY = "ШОССЕ"
    LANE = "ПЕРЕУЛОК"
    MICRODISTRICT = "МИКРОРАЙОН"
    MILITARY_TOWN = "ВОЕННЫЙ ГОРОДОК"
    MILITARY_UNIT = "ВОИНСКАЯ ЧАСТЬ"
    PARK = "ПАРК"
    RING = "КОЛЬЦО"
    SQUARE = "ПЛОЩАДЬ"
    STATION = "СТАНЦИЯ"
    TERRITORY = "ТЕРРИТОРИЯ"
    TRACT = "ТРАКТ"
    VILLAGE = "ПОСЕЛОК"

# Перечисления для типов населенных пунктов (отсортировано)
class CityType(enum.Enum):
    NONE = "НЕТ"
    AGROTOWN = "АГРОГОРОДОК"
    CITY = "ГОРОД"
    FARM = "ХУТОР"
    RESORT_SETTLEMENT = "КУРОРТНЫЙ ПОСЕЛОК"
    RURAL_COUNCIL = "СЕЛЬСОВЕТ"
    SELO = "СЕЛО"
    SETTLEMENT = "ПОСЕЛОК"
    SPECIAL_ECONOMIC_ZONE = "ОСОБАЯ ЭКОНОМИЧЕСКАЯ ЗОНА"
    URBAN_SETTLEMENT = "ГОРОДСКОЙ ПОСЕЛОК"
    VILLAGE = "ДЕРЕВНЯ"
    WORKERS_SETTLEMENT = "РАБОЧИЙ ПОСЕЛОК"