from sqlalchemy import String, Integer, Enum, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.engine import URL, Engine, create_engine
from enum import Enum as PyEnum
import os
from config import settings


def get_database_engine(echo: bool = True) -> Engine:
    url_db = settings.db.connection_string
    engine = create_engine(url_db, echo=echo)
    return engine

# Перечисления для типов улиц (отсортировано)
class StreetTypeDB(PyEnum):
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
    STREET = "УЛИЦА"
    TERRITORY = "ТЕРРИТОРИЯ"
    TRACT = "ТРАКТ"
    VILLAGE = "ПОСЕЛОК"

# Перечисления для типов населенных пунктов (отсортировано)
class CityTypeDB(PyEnum):
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

class Base(DeclarativeBase):
    pass

class BelpostAddress(Base):
    __tablename__ = "belpost_addresses"
    
    address_id: Mapped[int] = mapped_column(Integer, ForeignKey("addresses.id"), primary_key=True, nullable=False,
                                            autoincrement=False)
    address: Mapped["Address"] = relationship("Address", back_populates="belpost_address")
    
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)        # Наименование населенного пункта
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)      # Область
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)    # Район
    streetType: Mapped[StreetTypeDB | None] = mapped_column(Enum(StreetTypeDB), nullable=True)   # Тип улицы
    street: Mapped[str | None] = mapped_column(String(150), nullable=True)      # Улица
    house: Mapped[str | None] = mapped_column(String(20), nullable=True)        # Дом
    building: Mapped[str | None] = mapped_column(String(20), nullable=True)     # Корпус
    flat: Mapped[str | None] = mapped_column(String(20), nullable=True)         # Квартира
    cityType: Mapped[CityTypeDB | None] = mapped_column(Enum(CityTypeDB), nullable=True)     # Тип населенного пункта
    postcode: Mapped[str | None] = mapped_column(String(6), nullable=True)      # Почтовый индекс

    def __repr__(self) -> str:
        return (f"<BelpostAddress(id={self.address_id}, city={self.city}, region={self.region}, district={self.district}, "
                f"streetType={self.streetType}, street={self.street}, house={self.house}, "
                f"building={self.building}, flat={self.flat}, cityType={self.cityType}, "
                f"postcode={self.postcode})>")
        
class Address(Base):
    __tablename__ = "addresses" 
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    
    street: Mapped[str | None] = mapped_column(String(300), nullable=True)          # Улица, проспект и др.
    building: Mapped[str | None] = mapped_column(String(20), nullable=True)         # Корпус, дом, помещение и др.
    soato_imns: Mapped[int | None] = mapped_column(Integer, nullable=True)          # СОАТО ИМНС
    soato_oblast: Mapped[int | None] = mapped_column(String(20), nullable=True)     # СОАТО Область
    soato_district: Mapped[int | None] = mapped_column(String(50), nullable=True)   # СОАТО Район
    soato_sovet: Mapped[int | None] = mapped_column(String(50), nullable=True)      # СОАТО Сельсовет
    soato_tip: Mapped[str | None] = mapped_column(String(10), nullable=True)        # СОАТО Тип
    soato_name: Mapped[str | None] = mapped_column(String(50), nullable=True)       # СОАТО Наименование населенного пункта
    
    belpost_address: Mapped["BelpostAddress"] = relationship("BelpostAddress", back_populates="address")
    
    streetName: Mapped[str | None] = mapped_column(String(300), nullable=True)   # Название улицы, проспекта и др.
    streetType: Mapped[str | None] = mapped_column(String(100), nullable=True)    # Тип улицы (улица, проспект, переулок и др.)
    
    def __repr__(self) -> str:
        return (f"<Address(id={self.id}, street={self.street}, building={self.building} ... >")