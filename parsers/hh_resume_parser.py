"""
Парсер резюме кандидатов с hh.ru
"""
import logging
from datetime import datetime
from typing import Optional, List

from .base_parser import BaseParser, VacancyData
from config import get_role_by_keywords, get_level_by_keywords, IT_ROLES, Level

logger = logging.getLogger(__name__)


class HHResumeParser(BaseParser):
    """Парсер резюме hh.ru"""
    
    BASE_URL = "https://api.hh.ru/resumes"
    SOURCE_NAME = "hh.ru"
    
    def __init__(self, delay: float = 1.5):
        super().__init__(delay=delay)
    
    def _get_search_text(self, role_id: str) -> str:
        """Получить поисковый запрос для роли"""
        role_info = IT_ROLES.get(role_id, {})
        return role_info.get("name", role_id)
    
    def _parse_salary(self, item: dict) -> tuple[Optional[int], Optional[int], str]:
        """Парсинг зарплаты из резюме"""
        salary = item.get('salary', {})
        if not salary:
            return None, None, 'RUB'
        
        currency = salary.get('currency', 'RUB')
        salary_amount = salary.get('amount')
        
        if salary_amount:
            salary_amount, currency = self._normalize_salary(salary_amount, currency)
            return salary_amount, salary_amount, currency
        
        return None, None, 'RUB'
    
    def _parse_experience(self, item: dict) -> tuple[int, str]:
        """Парсинг опыта работы"""
        experience = item.get('experience', {})
        experience_id = experience.get('id', '') if experience else ''
        
        # Маппинг ID опыта hh.ru в годы
        experience_map = {
            'noExperience': 0,
            'between1And3': 2,
            'between3And6': 4,
            'moreThan6': 7,
        }
        
        years = experience_map.get(experience_id, 0)
        description = experience.get('name', '') if experience else ''
        
        return years, description
    
    def _parse_resume(self, item: dict, role_id: str) -> Optional[dict]:
        """Парсинг одного резюме"""
        try:
            title = item.get('title', '')
            
            # Определение уровня
            experience_years, experience_desc = self._parse_experience(item)
            level = self._detect_level_by_experience(experience_years)
            
            # Город
            area = item.get('area', {})
            city = area.get('name', 'Россия') if area else 'Россия'
            city = self._detect_city(city)
            
            # Зарплата
            salary_min, salary_max, currency = self._parse_salary(item)
            
            # Навыки
            skills = item.get('skills', [])
            skills_list = [s.get('name', '') for s in skills] if skills else []
            
            # Дата обновления
            updated_at_str = item.get('updated_at', '')
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00')) if updated_at_str else datetime.utcnow()
            
            # URL
            resume_url = item.get('alternate_urls', {}).get('html', '')
            
            return {
                'title': title,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'currency': currency,
                'city': city,
                'experience_years': experience_years,
                'experience_description': experience_desc,
                'role_id': role_id,
                'level': level,
                'skills': ','.join(skills_list),
                'source': self.SOURCE_NAME,
                'url': resume_url,
                'published_at': updated_at,
                'updated_at': updated_at,
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга резюме: {e}")
            return None
    
    def _detect_level_by_experience(self, years: int) -> str:
        """Определение уровня по опыту"""
        if years >= 7:
            return Level.SENIOR.value
        elif years >= 4:
            return Level.MIDDLE.value
        elif years >= 2:
            return Level.JUNIOR.value
        else:
            return Level.JUNIOR.value
    
    def parse_resumes(self, role_id: str, city: str, pages: int = 5) -> List[dict]:
        """Парсинг резюме для роли"""
        resumes = []
        search_text = self._get_search_text(role_id)
        
        # Определение города для API
        area_id = self._get_area_id(city)
        
        for page in range(pages):
            try:
                params = {
                    'text': f'AND(title:"{search_text}")',
                    'area': area_id,
                    'page': page,
                    'per_page': 100,
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
                    resume_data = self._parse_resume(item, role_id)
                    if resume_data:
                        resumes.append(resume_data)
                
                total_pages = (data.get('found', 0) // 100) + 1
                if page + 1 >= min(total_pages, pages):
                    break
                
                self._delay()
                
            except Exception as e:
                logger.error(f"Ошибка при парсинге страницы {page}: {e}")
                break
        
        logger.info(f"HH Resumes: найдено {len(resumes)} резюме для {search_text} в {city}")
        return resumes
    
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
        return area_ids.get(city, '1')
