"""
Модель вакансии
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Vacancy(Base):
    """Модель вакансии"""
    
    __tablename__ = 'vacancies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Основная информация
    title = Column(String(500), nullable=False)
    company = Column(String(300), nullable=True)
    
    # Зарплата
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    currency = Column(String(10), default='RUB')
    
    # Локация
    city = Column(String(100), nullable=False, default='Россия')
    
    # Опыт
    experience = Column(String(200), nullable=True)
    
    # Роль и уровень
    role_id = Column(String(100), nullable=False, index=True)
    level = Column(String(50), nullable=False, index=True)  # junior, middle, senior, team_lead
    
    # Источник
    source = Column(String(50), nullable=False)
    url = Column(String(1000), nullable=True)
    
    # Время
    published_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Индексы для ускорения выборок
    __table_args__ = (
        Index('idx_role_city', 'role_id', 'city'),
        Index('idx_level_city', 'level', 'city'),
        Index('idx_published_at', 'published_at'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Vacancy {self.title} at {self.company} ({self.city})>"
    
    def to_dict(self) -> dict:
        """Конвертация в словарь"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'currency': self.currency,
            'city': self.city,
            'experience': self.experience,
            'role_id': self.role_id,
            'level': self.level,
            'source': self.source,
            'url': self.url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_parser_data(cls, data) -> 'Vacancy':
        """Создание модели из данных парсера"""
        return cls(
            title=data.title,
            company=data.company,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
            currency=data.currency,
            city=data.city,
            experience=data.experience,
            role_id=data.role_id,
            level=data.level.value,
            source=data.source,
            url=data.url,
            published_at=data.published_at,
        )
