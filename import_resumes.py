"""
Скрипт для импорта резюме из Excel/CSV файлов
Поддерживает форматы: .xlsx, .xls, .csv
"""
import pandas as pd
import logging
from datetime import datetime
from database import Database
from models.market import Resume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def import_resumes_from_excel(file_path: str, source: str = 'hr_analyst') -> int:
    """
    Импорт резюме из Excel файла
    
    Args:
        file_path: Путь к файлу
        source: Источник данных
    
    Returns:
        Количество импортированных записей
    """
    db = Database()
    session = db.get_session()
    
    try:
        # Чтение Excel файла
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        logger.info(f"Загружено {len(df)} строк из файла")
        
        imported_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Маппинг колонок (адаптируйте под вашу структуру)
                resume = Resume(
                    title=row.get('Должность', row.get('Position', '')),
                    salary_min=int(row.get('Зарплата от', row.get('Salary Min', 0))) or None,
                    salary_max=int(row.get('Зарплата до', row.get('Salary Max', 0))) or None,
                    currency='RUB',
                    city=row.get('Город', row.get('City', 'Москва')),
                    experience_years=int(row.get('Опыт работы (лет)', row.get('Experience', 0))) or 0,
                    experience_description=row.get('Описание опыта', ''),
                    role_id=map_role_id(row.get('Должность', '')),
                    level=map_level(row.get('Уровень', row.get('Level', ''))),
                    skills=row.get('Навыки', row.get('Skills', '')),
                    source=source,
                    url=row.get('Ссылка', row.get('URL', '')),
                    published_at=parse_date(row.get('Дата публикации', row.get('Date', ''))),
                    updated_at=datetime.utcnow(),
                )
                
                session.add(resume)
                imported_count += 1
                
                if (idx + 1) % 100 == 0:
                    logger.info(f"Обработано {idx + 1} резюме...")
                    
            except Exception as e:
                logger.error(f"Ошибка при импорте строки {idx}: {e}")
                continue
        
        session.commit()
        logger.info(f"✅ Импортировано {imported_count} резюме")
        
        return imported_count
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка импорта: {e}")
        return 0
        
    finally:
        session.close()
        db.close()


def map_role_id(position: str) -> str:
    """
    Маппинг названия должности в role_id
    
    Args:
        position: Название должности
    
    Returns:
        role_id
    """
    position_lower = str(position).lower()
    
    role_mapping = {
        'android': 'android_developer',
        'angular': 'angular_developer',
        'c#': 'csharp_developer',
        'c sharp': 'csharp_developer',
        'devops': 'devops',
        'flutter': 'flutter_developer',
        'golang': 'golang_developer',
        'go ': 'golang_developer',
        'database': 'database_developer',
        'ios': 'ios_developer',
        'java': 'java_spring_developer',
        'kotlin': 'kotlin_developer',
        'node.js': 'nodejs_developer',
        'nodejs': 'nodejs_developer',
        'php': 'php_developer',
        'python': 'python_developer',
        'react': 'react_developer',
        'ruby': 'ruby_developer',
        'vue': 'vuejs_developer',
        'c++': 'cpp_developer',
        'delphi': 'delphi_developer',
        'test': 'qa_engineer',
        'qa': 'qa_engineer',
        'automation': 'qa_automation',
        'ui/ux': 'ui_ux_designer',
        'designer': 'ui_ux_designer',
        'dba': 'dba_oracle',
        'system admin': 'system_admin',
        'support': 'tech_support_2_3',
        'project manager': 'project_manager',
        'scrum': 'scrum_master',
        'product owner': 'product_owner',
        'analyst': 'business_analyst',
        'data analyst': 'data_analyst_sql',
        'architect': 'system_architect',
    }
    
    for key, role_id in role_mapping.items():
        if key in position_lower:
            return role_id
    
    return 'other'


def map_level(level_str: str) -> str:
    """
    Маппинг уровня специалиста
    
    Args:
        level_str: Строка уровня
    
    Returns:
        level (junior/middle/senior/team_lead)
    """
    level_lower = str(level_str).lower()
    
    if 'team' in level_lower or 'lead' in level_lower or 'head' in level_lower:
        return 'team_lead'
    elif 'senior' in level_lower or 'sr' in level_lower or 'ведущий' in level_lower:
        return 'senior'
    elif 'middle' in level_lower or 'mid' in level_lower or 'средний' in level_lower:
        return 'middle'
    elif 'junior' in level_lower or 'jun' in level_lower or 'начинающий' in level_lower:
        return 'junior'
    else:
        return 'middle'  # По умолчанию


def parse_date(date_str) -> datetime:
    """
    Парсинг даты из различных форматов
    
    Args:
        date_str: Строка даты
    
    Returns:
        datetime объект
    """
    if not date_str:
        return datetime.utcnow()
    
    formats = [
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%d/%m/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%d.%m.%Y %H:%M:%S',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except ValueError:
            continue
    
    return datetime.utcnow()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python import_resumes.py <путь_к_файлу> [источник]")
        print("Пример: python import_resumes.py resumes.xlsx hr_analyst")
        sys.exit(1)
    
    file_path = sys.argv[1]
    source = sys.argv[2] if len(sys.argv) > 2 else 'hr_analyst'
    
    print(f"🚀 Импорт резюме из {file_path}...")
    count = import_resumes_from_excel(file_path, source)
    print(f"✅ Готово! Импортировано {count} резюме")
