"""
Парсер Habr Career
"""
import re
import logging
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
from .base_parser import BaseParser, VacancyData
from config import IT_ROLES

logger = logging.getLogger(__name__)


class HabrParser(BaseParser):
    """Парсер habr.com/career"""
    
    BASE_URL = "https://habr.com/career/vacancies"
    SOURCE_NAME = "habr.career"
    
    def __init__(self, delay: float = 3.0):
        super().__init__(delay=delay)
    
    def _get_search_term(self, role_id: str) -> str:
        """Получить поисковый термин для роли"""
        role_info = IT_ROLES.get(role_id, {})
        return role_info.get("name", role_id)
    
    def _parse_salary_text(self, text: str) -> tuple[Optional[int], Optional[int], str]:
        """Парсинг зарплаты из текста"""
        if not text:
            return None, None, 'RUB'
        
        # Удаление пробелов между цифрами
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
        
        # Поиск чисел
        numbers = re.findall(r'(\d+(?:\s*\d+)*)', text)
        numbers = [int(n.replace(' ', '')) for n in numbers if n]
        
        # Определение валюты
        currency = 'RUB'
        if '$' in text or 'USD' in text.upper():
            currency = 'USD'
        elif '€' in text or 'EUR' in text.upper():
            currency = 'EUR'
        
        if len(numbers) >= 2:
            salary_min, salary_max = numbers[0], numbers[1]
        elif len(numbers) == 1:
            salary_min = numbers[0]
            salary_max = None
        else:
            return None, None, 'RUB'
        
        # Нормализация
        salary_min, currency = self._normalize_salary(salary_min, currency)
        if salary_max:
            salary_max, _ = self._normalize_salary(salary_max, currency)
        
        return salary_min, salary_max, currency
    
    def _parse_vacancy_card(self, card, role_id: str) -> Optional[VacancyData]:
        """Парсинг карточки вакансии"""
        try:
            # Заголовок
            title_elem = card.find('a', class_='vacancy-card__title')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            
            # URL
            url = title_elem.get('href', '')
            if url.startswith('/'):
                url = f'https://habr.com{url}'
            
            # Компания
            company_elem = card.find('span', class_='vacancy-card__company')
            company = company_elem.get_text(strip=True) if company_elem else 'Не указано'
            
            # Зарплата
            salary_elem = card.find('div', class_='vacancy-card__salary')
            salary_text = salary_elem.get_text(strip=True) if salary_elem else ''
            salary_min, salary_max, currency = self._parse_salary_text(salary_text)
            
            # Город и опыт
            meta_elems = card.find_all('span', class_='vacancy-card__meta-text')
            city = 'Россия'
            experience = ''
            
            for elem in meta_elems:
                text = elem.get_text(strip=True)
                if text:
                    city = self._detect_city(text)
                    if city != 'Россия':
                        break
            
            # Опыт из данных карточки
            experience_elem = card.find('span', string=re.compile('опыт|лет', re.I))
            if experience_elem:
                experience = experience_elem.get_text(strip=True)
            
            # Определение уровня
            level = self._detect_level(title, experience)
            
            # Дата (берем текущую, т.к. habr не всегда показывает)
            published_at = datetime.now()
            
            return VacancyData(
                title=title,
                company=company,
                salary_min=salary_min,
                salary_max=salary_max,
                currency=currency,
                city=city,
                experience=experience,
                role_id=role_id,
                level=level,
                source=self.SOURCE_NAME,
                url=url,
                published_at=published_at,
            )
            
        except Exception as e:
            logger.error(f"Ошибка парсинга карточки: {e}")
            return None
    
    def parse(self, role_id: str, city: str, pages: int = 5) -> list[VacancyData]:
        """Парсинг вакансий для роли"""
        vacancies = []
        search_term = self._get_search_term(role_id)
        
        # Город для URL
        city_slug = self._get_city_slug(city)
        
        for page in range(1, pages + 1):
            try:
                url = f"{self.BASE_URL}{city_slug}/?page={page}&q={search_term}"
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"Habr вернул статус {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Поиск карточек вакансий
                cards = soup.find_all('article', class_='vacancy-card')
                
                if not cards:
                    break
                
                for card in cards:
                    vacancy = self._parse_vacancy_card(card, role_id)
                    if vacancy:
                        vacancies.append(vacancy)
                
                self._delay()
                
            except Exception as e:
                logger.error(f"Ошибка при парсинге страницы {page}: {e}")
                break
        
        logger.info(f"Habr: найдено {len(vacancies)} вакансий для {search_term} в {city}")
        return vacancies
    
    def _get_city_slug(self, city: str) -> str:
        """Получить slug города для URL"""
        city_slugs = {
            'Москва': '/moscow',
            'Санкт-Петербург': '/sanct-peterburg',
            'Екатеринбург': '/ekaterinburg',
            'Новосибирск': '/novosibirsk',
            'Казань': '/kazan',
            'Нижний Новгород': '/nizhniy-novgorod',
            'Челябинск': '/chelyabinsk',
            'Самара': '/samara',
            'Уфа': '/ufa',
            'Ростов-на-Дону': '/rostov-na-donu',
        }
        return city_slugs.get(city, '')  # Пустая строка = все города
