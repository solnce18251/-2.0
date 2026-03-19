"""
Скрипт для импорта резюме из Google Sheets
"""
import logging
import requests
from io import BytesIO
import pandas as pd
from database import Database
from import_resumes import map_role_id, map_level, parse_date
from models.market import Resume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def import_from_google_sheets(sheet_id: str, gid: str = '0') -> int:
    """
    Импорт резюме из Google Sheets
    
    Args:
        sheet_id: ID документа Google Sheets
        gid: ID листа (gid)
    
    Returns:
        Количество импортированных записей
    """
    db = Database()
    session = db.get_session()
    
    try:
        # Формирование URL для экспорта в CSV
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        
        logger.info(f"Загрузка данных из Google Sheets: {export_url}")
        
        # Загрузка данных
        response = requests.get(export_url)
        response.raise_for_status()
        
        # Чтение CSV
        df = pd.read_csv(BytesIO(response.content))
        
        logger.info(f"Загружено {len(df)} строк из Google Sheets")
        
        imported_count = 0
        
        for idx, row in df.iterrows():
            try:
                resume = Resume(
                    title=str(row.get('Должность', row.get('Position', ''))),
                    salary_min=int(row.get('Зарплата от', row.get('Salary Min', 0))) or None,
                    salary_max=int(row.get('Зарплата до', row.get('Salary Max', 0))) or None,
                    currency='RUB',
                    city=str(row.get('Город', row.get('City', 'Москва'))),
                    experience_years=int(row.get('Опыт работы (лет)', row.get('Experience', 0))) or 0,
                    experience_description=str(row.get('Описание опыта', '')),
                    role_id=map_role_id(row.get('Должность', '')),
                    level=map_level(row.get('Уровень', row.get('Level', ''))),
                    skills=str(row.get('Навыки', row.get('Skills', ''))),
                    source='google_sheets_import',
                    url=str(row.get('Ссылка', row.get('URL', ''))),
                    published_at=parse_date(row.get('Дата публикации', row.get('Date', ''))),
                    updated_at=None,
                )
                
                session.add(resume)
                imported_count += 1
                
                if (idx + 1) % 100 == 0:
                    logger.info(f"Обработано {idx + 1} резюме...")
                    
            except Exception as e:
                logger.error(f"Ошибка при импорте строки {idx}: {e}")
                continue
        
        session.commit()
        logger.info(f"✅ Импортировано {imported_count} резюме из Google Sheets")
        
        return imported_count
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка импорта из Google Sheets: {e}")
        return 0
        
    finally:
        session.close()
        db.close()


if __name__ == '__main__':
    # ID документа из ссылки
    SHEET_ID = '1bAkVtcOmogpa6Cgeo365MrL7hbSRLpiN'
    GID = '1912705233'  # ID листа
    
    print(f"🚀 Импорт резюме из Google Sheets...")
    count = import_from_google_sheets(SHEET_ID, GID)
    print(f"✅ Готово! Импортировано {count} резюме")
