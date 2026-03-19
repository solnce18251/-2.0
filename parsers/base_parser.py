"""
Базовый класс для всех парсеров
"""
import time
import random
import logging
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from config import Level, CITIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VacancyData:
    """Структура данных о вакансии"""
    title: str
    company: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    currency: str
    city: str
    experience: str
    role_id: str
    level: Level
    source: str
    url: str
    published_at: datetime
    raw_description: str = ""


class BaseParser(ABC):
    """Базовый класс парсера"""
    
    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Настройка HTTP сессии"""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.session = requests.Session()
        
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        
        # Заголовки для имитации браузера
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })
    
    def _delay(self):
        """Случайная задержка между запросами"""
        time.sleep(self.delay + random.uniform(0.5, 1.5))
    
    def _normalize_salary(self, amount: Optional[int], currency: str) -> tuple[Optional[int], str]:
        """
        Нормализация зарплаты к RUB
        """
        if amount is None:
            return None, 'RUB'
        
        # Курсы валют (примерные, можно обновлять из API)
        exchange_rates = {
            'USD': 92.0,
            'EUR': 100.0,
            'BYN': 28.0,
            'KZT': 0.2,
            'RUB': 1.0,
        }
        
        rate = exchange_rates.get(currency.upper(), 1.0)
        converted = int(amount * rate)
        
        return converted, 'RUB'
    
    def _detect_level(self, title: str, experience: str) -> Level:
        """Определение уровня позиции"""
        from config import LEVEL_KEYWORDS
        
        text = f"{title} {experience}".lower()
        
        # Team Lead
        for kw in LEVEL_KEYWORDS[Level.TEAM_LEAD]:
            if kw in text:
                return Level.TEAM_LEAD
        
        # Senior
        for kw in LEVEL_KEYWORDS[Level.SENIOR]:
            if kw in text:
                return Level.SENIOR
        
        # Middle
        for kw in LEVEL_KEYWORDS[Level.MIDDLE]:
            if kw in text:
                return Level.MIDDLE
        
        return Level.JUNIOR
    
    def _detect_city(self, text: str) -> str:
        """Определение города из текста"""
        text_lower = text.lower()
        
        # Приоритет: Москва и СПб
        if 'москва' in text_lower:
            return 'Москва'
        if 'санкт-петербург' in text_lower or 'спб' in text_lower:
            return 'Санкт-Петербург'
        
        # Другие города
        for city in CITIES:
            if city.lower() in text_lower:
                return city
        
        return 'Россия'  # По умолчанию
    
    @abstractmethod
    def parse(self, role_id: str, city: str, pages: int = 5) -> list[VacancyData]:
        """
        Парсинг вакансий
        
        Args:
            role_id: ID роли для поиска
            city: Город для поиска
            pages: Количество страниц для парсинга
        
        Returns:
            Список вакансий
        """
        pass
    
    def close(self):
        """Закрытие сессии"""
        if self.session:
            self.session.close()
