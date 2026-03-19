"""
Парсер HeadHunter (hh.ru)
"""
import re
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from .base_parser import BaseParser, VacancyData
from config import get_role_by_keywords, get_level_by_keywords, IT_ROLES

logger = logging.getLogger(__name__)


class HHParser(BaseParser):
    """Парсер hh.ru"""
    
    BASE_URL = "https://api.hh.ru/vacancies"
    SOURCE_NAME = "hh.ru"
    
    def __init__(self, delay: float = 1.0):
        super().__init__(delay=delay)
    
    def _get_role_query(self, role_id: str) -> str:
        """Получить поисковый запрос для роли"""
        role_info = IT_ROLES.get(role_id, {})
        return role_info.get("name", role_id)
    
    def _parse_salary(self, item: dict) -> tuple[Optional[int], Optional[int], str]:
        """Парсинг зарплаты из данных hh"""
        salary = item.get('salary', {})
        if not salary:
            return None, None, 'RUB'
        
        currency = salary.get('currency', 'RUB')
        salary_min = salary.get('from')
        salary_max = salary.get('to')
        
        # Нормализация
        if salary_min:
            salary_min, currency = self._normalize_salary(salary_min, currency)
        if salary_max:
            salary_max, currency = self._normalize_salary(salary_max, currency)
        
        return salary_min, salary_max, currency
    
    def _parse_vacancy(self, item: dict, role_id: str) -> Optional[VacancyData]:
        """Парсинг одной вакансии"""
        try:
            title = item.get('name', '')
            
            # Определение уровня
            experience_name = item.get('experience', {}).get('name', '') if item.get('experience') else ''
            level = self._detect_level(title, experience_name)
            
            # Город
            area = item.get('area', {}).get('name', '') if item.get('area') else ''
            city = self._detect_city(area)
            
            # Зарплата
            salary_min, salary_max, currency = self._parse_salary(item)
            
            # Дата публикации
            published_at_str = item.get('published_at', '')
            published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            
            # Компания
            employer = item.get('employer', {})
            company = employer.get('name', '') if employer else 'Не указано'
            
            # URL
            vacancy_url = item.get('alternate_urls', {}).get('html', '')
            
            return VacancyData(
                title=title,
                company=company,
                salary_min=salary_min,
                salary_max=salary_max,
                currency=currency,
                city=city,
                experience=experience_name,
                role_id=role_id,
                level=level,
                source=self.SOURCE_NAME,
                url=vacancy_url,
                published_at=published_at,
            )
        except Exception as e:
            logger.error(f"Ошибка парсинга вакансии: {e}")
            return None
    
    def parse(self, role_id: str, city: str, pages: int = 5) -> list[VacancyData]:
        """Парсинг вакансий для роли"""
        vacancies = []
        role_query = self._get_role_query(role_id)
        
        # Определение города для API
        area_id = self._get_area_id(city)
        
        for page in range(pages):
            try:
                params = {
                    'text': f'NAME:{role_query}',
                    'area': area_id,
                    'page': page,
                    'per_page': 100,
                    'only_with_salary': 'true',
                }
                
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"HH вернул статус {response.status_code}")
                    break
                
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                for item in items:
                    vacancy = self._parse_vacancy(item, role_id)
                    if vacancy:
                        vacancies.append(vacancy)
                
                total_pages = (data.get('found', 0) // 100) + 1
                if page + 1 >= min(total_pages, pages):
                    break
                
                self._delay()
                
            except Exception as e:
                logger.error(f"Ошибка при парсинге страницы {page}: {e}")
                break
        
        logger.info(f"HH: найдено {len(vacancies)} вакансий для {role_query} в {city}")
        return vacancies
    
    def _get_area_id(self, city: str) -> str:
        """Получить ID области для города"""
        area_ids = {
            'Москва': '1',
            'Санкт-Петербург': '2',
            'Екатеринбург': '3',
            'Новосибирск': '4',
            'Казань': '77',
            'Нижний Новгород': '54',
            'Челябинск': '80',
            'Самара': '57',
            'Уфа': '102',
            'Ростов-на-Дону': '116',
        }
        return area_ids.get(city, '1')  # По умолчанию Москва
