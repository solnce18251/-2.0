"""
Модуль работы с базой данных
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from config import DATABASE_URL
from models.vacancy import Vacancy, Base

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or DATABASE_URL
        self.engine = None
        self.SessionLocal = None
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных"""
        # Для SQLite используем StaticPool для совместимости с threading
        if self.db_url.startswith('sqlite'):
            self.engine = create_engine(
                self.db_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            self.engine = create_engine(self.db_url, echo=False)
        
        # Создание таблиц
        Base.metadata.create_all(bind=self.engine)
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info("База данных инициализирована")
    
    def get_session(self) -> Session:
        """Получение сессии"""
        return self.SessionLocal()
    
    def add_vacancy(self, vacancy: Vacancy) -> int:
        """Добавление вакансии"""
        session = self.get_session()
        try:
            session.add(vacancy)
            session.commit()
            session.refresh(vacancy)
            return vacancy.id
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка добавления вакансии: {e}")
            return -1
        finally:
            session.close()
    
    def add_vacancies_batch(self, vacancies: list[Vacancy]) -> int:
        """
        Пакетное добавление вакансий
        
        Returns:
            Количество добавленных записей
        """
        session = self.get_session()
        try:
            # Проверка на дубликаты по URL
            existing_urls = set()
            if vacancies:
                urls = [v.url for v in vacancies if v.url]
                if urls:
                    existing = session.query(Vacancy.url).filter(
                        Vacancy.url.in_(urls)
                    ).all()
                    existing_urls = {row[0] for row in existing}
            
            # Добавление новых
            new_vacancies = []
            for v in vacancies:
                if not v.url or v.url not in existing_urls:
                    new_vacancies.append(v)
            
            if new_vacancies:
                session.bulk_save_objects(new_vacancies)
                session.commit()
                logger.info(f"Добавлено {len(new_vacancies)} вакансий")
                return len(new_vacancies)
            
            return 0
            
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка пакетного добавления: {e}")
            return 0
        finally:
            session.close()
    
    def get_vacancies_filtered(self,
                                role_ids: Optional[list[str]] = None,
                                levels: Optional[list[str]] = None,
                                cities: Optional[list[str]] = None,
                                date_from: Optional[datetime] = None,
                                date_to: Optional[datetime] = None,
                                limit: int = 1000) -> list[Vacancy]:
        """Получение вакансий с фильтрами"""
        session = self.get_session()
        try:
            query = session.query(Vacancy)
            
            filters = []
            
            if role_ids:
                filters.append(Vacancy.role_id.in_(role_ids))
            
            if levels:
                filters.append(Vacancy.level.in_(levels))
            
            if cities:
                filters.append(Vacancy.city.in_(cities))
            
            if date_from:
                filters.append(Vacancy.published_at >= date_from)
            
            if date_to:
                filters.append(Vacancy.published_at <= date_to)
            
            if filters:
                query = query.filter(and_(*filters))
            
            # Сортировка по дате публикации
            query = query.order_by(Vacancy.published_at.desc())
            
            vacancies = query.limit(limit).all()
            return vacancies
            
        except Exception as e:
            logger.error(f"Ошибка получения вакансий: {e}")
            return []
        finally:
            session.close()
    
    def get_salary_statistics(self,
                               role_ids: Optional[list[str]] = None,
                               levels: Optional[list[str]] = None,
                               cities: Optional[list[str]] = None,
                               date_from: Optional[datetime] = None,
                               date_to: Optional[datetime] = None) -> dict:
        """
        Получение статистики по зарплатам
        
        Returns:
            Словарь со статистикой: count, min, p25, median, p75, max, average
        """
        session = self.get_session()
        try:
            # Базовый запрос
            query = session.query(Vacancy.salary_min, Vacancy.salary_max)
            
            filters = []
            
            if role_ids:
                filters.append(Vacancy.role_id.in_(role_ids))
            
            if levels:
                filters.append(Vacancy.level.in_(levels))
            
            if cities:
                # Москва и Россия как синонимы для статистики
                if 'Россия' in cities:
                    cities_filter = cities.copy()
                else:
                    cities_filter = cities
                filters.append(Vacancy.city.in_(cities_filter))
            
            if date_from:
                filters.append(Vacancy.published_at >= date_from)
            
            if date_to:
                filters.append(Vacancy.published_at <= date_to)
            
            if filters:
                query = query.filter(and_(*filters))
            
            results = query.all()
            
            if not results:
                return {'count': 0}
            
            # Вычисление средней зарплаты для каждой вакансии
            salaries = []
            for salary_min, salary_max in results:
                if salary_min and salary_max:
                    salaries.append((salary_min + salary_max) / 2)
                elif salary_min:
                    salaries.append(salary_min)
                elif salary_max:
                    salaries.append(salary_max)
            
            if not salaries:
                return {'count': len(results)}
            
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
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {'count': 0}
        finally:
            session.close()
    
    def get_all_roles_with_data(self) -> list[str]:
        """Получение всех ролей, по которым есть данные"""
        session = self.get_session()
        try:
            result = session.query(Vacancy.role_id).distinct().all()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Ошибка получения ролей: {e}")
            return []
        finally:
            session.close()
    
    def get_all_cities_with_data(self) -> list[str]:
        """Получение всех городов с данными"""
        session = self.get_session()
        try:
            result = session.query(Vacancy.city).distinct().all()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Ошибка получения городов: {e}")
            return []
        finally:
            session.close()
    
    def get_date_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Получение диапазона дат в базе"""
        session = self.get_session()
        try:
            min_date = session.query(func.min(Vacancy.published_at)).scalar()
            max_date = session.query(func.max(Vacancy.published_at)).scalar()
            return min_date, max_date
        except Exception as e:
            logger.error(f"Ошибка получения диапазона дат: {e}")
            return None, None
        finally:
            session.close()
    
    def get_vacancy_count(self) -> int:
        """Получение общего количества вакансий"""
        session = self.get_session()
        try:
            return session.query(Vacancy).count()
        except Exception as e:
            logger.error(f"Ошибка получения количества: {e}")
            return 0
        finally:
            session.close()
    
    def clear_old_data(self, days: int = 90):
        """Удаление старых данных"""
        session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = session.query(Vacancy).filter(
                Vacancy.published_at < cutoff_date
            ).delete(synchronize_session=False)
            session.commit()
            logger.info(f"Удалено {deleted} старых записей")
            return deleted
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка удаления старых данных: {e}")
            return 0
        finally:
            session.close()
    
    def close(self):
        """Закрытие соединения"""
        if self.engine:
            self.engine.dispose()
