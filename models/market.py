"""
Модели данных для резюме и статистики рынка
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Resume(Base):
    """Модель резюме кандидата"""
    
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Основная информация
    title = Column(String(500), nullable=False)
    
    # Зарплатные ожидания
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    currency = Column(String(10), default='RUB')
    
    # Локация
    city = Column(String(100), nullable=False, default='Россия')
    
    # Опыт
    experience_years = Column(Integer, nullable=True)  # лет опыта
    experience_description = Column(String(500), nullable=True)
    
    # Роль и уровень
    role_id = Column(String(100), nullable=False, index=True)
    level = Column(String(50), nullable=False, index=True)
    
    # Навыки
    skills = Column(Text, nullable=True)  # JSON список навыков
    
    # Источник
    source = Column(String(50), nullable=False)
    url = Column(String(1000), nullable=True)
    
    # Время
    published_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Индексы
    __table_args__ = (
        Index('idx_resume_role_city', 'role_id', 'city'),
        Index('idx_resume_level', 'level'),
        Index('idx_resume_published', 'published_at'),
    )
    
    def __repr__(self):
        return f"<Resume {self.title} ({self.city})>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'currency': self.currency,
            'city': self.city,
            'experience_years': self.experience_years,
            'role_id': self.role_id,
            'level': self.level,
            'source': self.source,
            'url': self.url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }


class VacancyStatistic(Base):
    """Статистика по вакансиям (снимок на дату)"""
    
    __tablename__ = 'vacancy_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Параметры выборки
    role_id = Column(String(100), nullable=False, index=True)
    level = Column(String(50), nullable=False, index=True)
    city = Column(String(100), nullable=False)
    
    # Количество вакансий
    vacancy_count = Column(Integer, default=0)
    
    # Зарплатная статистика
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_median = Column(Integer, nullable=True)
    salary_average = Column(Integer, nullable=True)
    salary_p25 = Column(Integer, nullable=True)
    salary_p75 = Column(Integer, nullable=True)
    currency = Column(String(10), default='RUB')
    
    # Дата снимка
    snapshot_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_vac_stat_role_level_city', 'role_id', 'level', 'city'),
        Index('idx_vac_stat_date', 'snapshot_date'),
    )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'role_id': self.role_id,
            'level': self.level,
            'city': self.city,
            'vacancy_count': self.vacancy_count,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_median': self.salary_median,
            'salary_average': self.salary_average,
            'salary_p25': self.salary_p25,
            'salary_p75': self.salary_p75,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
        }


class ResumeStatistic(Base):
    """Статистика по резюме (снимок на дату)"""
    
    __tablename__ = 'resume_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Параметры выборки
    role_id = Column(String(100), nullable=False, index=True)
    level = Column(String(50), nullable=False, index=True)
    city = Column(String(100), nullable=False)
    
    # Количество резюме
    resume_count = Column(Integer, default=0)
    
    # Зарплатные ожидания
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_median = Column(Integer, nullable=True)
    salary_average = Column(Integer, nullable=True)
    salary_p25 = Column(Integer, nullable=True)
    salary_p75 = Column(Integer, nullable=True)
    currency = Column(String(10), default='RUB')
    
    # Дата снимка
    snapshot_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_res_stat_role_level_city', 'role_id', 'level', 'city'),
        Index('idx_res_stat_date', 'snapshot_date'),
    )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'role_id': self.role_id,
            'level': self.level,
            'city': self.city,
            'resume_count': self.resume_count,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_median': self.salary_median,
            'salary_average': self.salary_average,
            'salary_p25': self.salary_p25,
            'salary_p75': self.salary_p75,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
        }
