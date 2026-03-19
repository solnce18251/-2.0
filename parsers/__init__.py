"""
Модуль парсинга данных о зарплатах
"""
from .base_parser import BaseParser
from .hh_parser import HHParser
from .habr_parser import HabrParser
from .data_collector import DataCollector

__all__ = ['BaseParser', 'HHParser', 'HabrParser', 'DataCollector']
