"""
Скрипт для генерации тестовых данных
Запустите для демонстрации работы дашборда
"""
import random
from datetime import datetime, timedelta
from database import Database
from models.vacancy import Vacancy
from config import IT_ROLES, Level, CITIES

def generate_test_data(vacancies_count: int = 500):
    """Генерация тестовых данных"""
    
    db = Database()
    
    # Базовые зарплаты по ролям (медиана)
    base_salaries = {
        # Разработка - высокие зарплаты
        'python_developer': 180000,
        'java_spring_developer': 200000,
        'golang_developer': 220000,
        'javascript_developer': 170000,
        'react_developer': 180000,
        'nodejs_developer': 190000,
        'php_developer': 140000,
        'csharp_developer': 170000,
        'android_developer': 180000,
        'ios_developer': 190000,
        'devops': 230000,
        
        # Тестирование
        'qa_engineer': 120000,
        'qa_mobile': 140000,
        'qa_automation': 180000,
        
        # Дизайн
        'ui_ux_designer': 150000,
        
        # Инженеры
        'system_admin': 130000,
        'dba_oracle': 180000,
        'tech_support_2_3': 90000,
        
        # Управление проектами
        'project_manager': 200000,
        'scrum_master': 180000,
        'product_owner': 220000,
        
        # Анализ
        'business_analyst': 160000,
        'system_analyst': 180000,
        'data_analyst_sql': 150000,
        
        # Архитектура
        'system_architect': 280000,
    }
    
    # Множители по уровням
    level_multipliers = {
        Level.JUNIOR.value: 0.5,
        Level.MIDDLE.value: 0.85,
        Level.SENIOR.value: 1.3,
        Level.TEAM_LEAD.value: 1.6,
    }
    
    # Множители по городам
    city_multipliers = {
        'Москва': 1.2,
        'Санкт-Петербург': 1.0,
        'Екатеринбург': 0.85,
        'Новосибирск': 0.85,
        'Казань': 0.8,
        'Россия': 0.9,
    }
    
    companies = [
        'Яндекс', 'Сбер', 'Тинькофф', 'VK', 'Ozon', 'Wildberries',
        'МТС', 'Билайн', 'Мегафон', 'Лаборатория Касперского',
        '1С', 'Ростелеком', 'Газпромнефть', 'Лукойл', 'Сибур',
        'Техноком', 'Иннополис', 'Точка', 'Контур', 'Битрикс',
        'JetBrains', 'Acronis', 'Nginx', 'Veeam', 'Kaspersky'
    ]
    
    created_count = 0
    
    for i in range(vacancies_count):
        # Выбор случайной роли
        role_id = random.choice(list(IT_ROLES.keys()))
        
        # Выбор уровня с весами (больше middle и senior)
        level = random.choices(
            [Level.JUNIOR.value, Level.MIDDLE.value, Level.SENIOR.value, Level.TEAM_LEAD.value],
            weights=[15, 40, 35, 10]
        )[0]
        
        # Выбор города
        city = random.choice(CITIES[:6])
        
        # Расчет зарплаты
        base = base_salaries.get(role_id, 150000)
        level_mult = level_multipliers.get(level, 1.0)
        city_mult = city_multipliers.get(city, 1.0)
        
        # Разброс зарплаты ±20%
        variance = random.uniform(0.8, 1.2)
        salary = int(base * level_mult * city_mult * variance)
        
        # Разделение на min/max
        salary_min = int(salary * random.uniform(0.85, 0.95))
        salary_max = int(salary * random.uniform(1.05, 1.2))
        
        # Дата публикации (последние 90 дней)
        days_ago = random.randint(0, 90)
        published_at = datetime.utcnow() - timedelta(days=days_ago)
        
        vacancy = Vacancy(
            title=f"{IT_ROLES[role_id]['name']} ({level.capitalize()})",
            company=random.choice(companies),
            salary_min=salary_min,
            salary_max=salary_max,
            currency='RUB',
            city=city,
            experience=f"{level} level",
            role_id=role_id,
            level=level,
            source=random.choice(['hh.ru', 'habr.career']),
            url=f'https://example.com/vacancy/{i}',
            published_at=published_at,
        )
        
        db.add_vacancy(vacancy)
        created_count += 1
        
        if (i + 1) % 50 == 0:
            print(f"Создано {i + 1} вакансий...")
    
    print(f"\n✅ Создано {created_count} тестовых вакансий")
    db.close()


if __name__ == '__main__':
    print("🚀 Генерация тестовых данных...")
    generate_test_data(500)
    print("\nТеперь запустите сервер: python run.py server")
