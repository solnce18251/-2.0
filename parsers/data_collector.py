"""
Сборщик данных - агрегирует парсеры и управляет процессом сбора
"""
import logging
from datetime import datetime
from typing import Optional

from config import IT_ROLES, CITIES, Level
from .base_parser import VacancyData
from .hh_parser import HHParser
from .habr_parser import HabrParser

logger = logging.getLogger(__name__)


class DataCollector:
    """Класс для сбора данных о зарплатах"""
    
    def __init__(self):
        self.parsers = {
            'hh': HHParser(delay=1.5),
            'habr': HabrParser(delay=3.0),
        }
        self.collected_vacancies: list[VacancyData] = []
    
    def collect_for_role(self, role_id: str, city: str, 
                         sources: Optional[list[str]] = None,
                         pages_per_source: int = 5) -> list[VacancyData]:
        """
        Сбор вакансий для конкретной роли
        
        Args:
            role_id: ID роли
            city: Город
            sources: Список источников (hh, habr)
            pages_per_source: Количество страниц для каждого источника
        
        Returns:
            Список вакансий
        """
        if sources is None:
            sources = list(self.parsers.keys())
        
        vacancies = []
        
        for source_key in sources:
            parser = self.parsers.get(source_key)
            if not parser:
                logger.warning(f"Неизвестный источник: {source_key}")
                continue
            
            try:
                logger.info(f"Парсинг {source_key}: {role_id} в {city}")
                source_vacancies = parser.parse(
                    role_id=role_id,
                    city=city,
                    pages=pages_per_source
                )
                vacancies.extend(source_vacancies)
                
            except Exception as e:
                logger.error(f"Ошибка парсинга {source_key}: {e}")
        
        return vacancies
    
    def collect_all_roles(self, cities: Optional[list[str]] = None,
                          sources: Optional[list[str]] = None,
                          pages_per_source: int = 3) -> list[VacancyData]:
        """
        Сбор вакансий для всех ролей
        
        Args:
            cities: Список городов
            sources: Список источников
            pages_per_source: Количество страниц для каждого источника
        
        Returns:
            Список всех вакансий
        """
        if cities is None:
            cities = CITIES[:3]  # По умолчанию первые 3 города
        
        all_vacancies = []
        total_roles = len(IT_ROLES)
        current_role = 0
        
        for role_id in IT_ROLES.keys():
            current_role += 1
            logger.info(f"Обработка роли {current_role}/{total_roles}: {role_id}")
            
            for city in cities:
                vacancies = self.collect_for_role(
                    role_id=role_id,
                    city=city,
                    sources=sources,
                    pages_per_source=pages_per_source
                )
                all_vacancies.extend(vacancies)
                logger.info(f"  {city}: {len(vacancies)} вакансий")
        
        self.collected_vacancies = all_vacancies
        logger.info(f"Всего собрано вакансий: {len(all_vacancies)}")
        
        return all_vacancies
    
    def collect_for_city(self, city: str,
                         sources: Optional[list[str]] = None,
                         pages_per_source: int = 3) -> list[VacancyData]:
        """
        Сбор вакансий для конкретного города по всем ролям
        """
        all_vacancies = []
        
        for role_id in IT_ROLES.keys():
            vacancies = self.collect_for_role(
                role_id=role_id,
                city=city,
                sources=sources,
                pages_per_source=pages_per_source
            )
            all_vacancies.extend(vacancies)
        
        return all_vacancies
    
    def get_statistics(self, vacancies: list[VacancyData]) -> dict:
        """
        Подсчет базовой статистики по вакансиям
        
        Returns:
            Словарь со статистикой
        """
        if not vacancies:
            return {'count': 0}
        
        salaries = []
        for v in vacancies:
            if v.salary_min and v.salary_max:
                salaries.append((v.salary_min + v.salary_max) / 2)
            elif v.salary_min:
                salaries.append(v.salary_min)
            elif v.salary_max:
                salaries.append(v.salary_max)
        
        if not salaries:
            return {'count': len(vacancies)}
        
        salaries.sort()
        n = len(salaries)
        
        # Персентили
        p25_idx = int(n * 0.25)
        p50_idx = int(n * 0.50)
        p75_idx = int(n * 0.75)
        
        return {
            'count': n,
            'min': int(salaries[0]),
            'p25': int(salaries[p25_idx]),
            'median': int(salaries[p50_idx]),
            'p75': int(salaries[p75_idx]),
            'max': int(salaries[-1]),
            'average': int(sum(salaries) / n),
        }
    
    def close(self):
        """Закрытие всех парсеров"""
        for parser in self.parsers.values():
            parser.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
