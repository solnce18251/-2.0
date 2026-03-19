"""
Скрипт для обновления данных в базе
Очищает старые данные и запускает парсинг заново
"""
import logging
import sys
from datetime import datetime, timedelta
from database import Database
from models.vacancy import Vacancy
from run import parse_all
from config import IT_ROLES, CITIES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clear_old_data(days: int = 0):
    """
    Очистка старых данных
    
    Args:
        days: Удалять данные старше этого количества дней (0 = все данные)
    """
    db = Database()
    session = db.get_session()
    
    try:
        if days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = session.query(Vacancy).filter(
                Vacancy.published_at < cutoff_date
            ).delete(synchronize_session=False)
            logger.info(f"Удалено {deleted} записей старше {days} дней")
        else:
            deleted = session.query(Vacancy).delete()
            logger.info(f"Удалено ВСЕХ {deleted} записей")
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка очистки: {e}")
    finally:
        session.close()
        db.close()


def refresh_data(clear: bool = False, roles: list = None, cities: list = None, pages: int = 3):
    """
    Обновление данных
    
    Args:
        clear: Очищать ли базу перед парсингом
        roles: Список ролей для парсинга
        cities: Список городов
        pages: Количество страниц для парсинга
    """
    if clear:
        logger.info("Очистка базы данных...")
        clear_old_data()
    
    logger.info("Запуск парсинга...")
    
    if roles is None:
        roles = list(IT_ROLES.keys())[:5]  # По умолчанию первые 5 ролей
        logger.info(f"Парсинг первых 5 ролей: {roles}")
    
    if cities is None:
        cities = ['Москва']
        logger.info(f"Парсинг по городам: {cities}")
    
    total = parse_all(roles=roles, cities=cities, pages=pages)
    
    logger.info(f"✅ Обновление завершено! Добавлено {total} вакансий")


if __name__ == '__main__':
    print("=" * 60)
    print("   Обновление данных парсера")
    print("=" * 60)
    print()
    print("Выберите действие:")
    print("1. Очистить базу и собрать заново (все роли, Москва, 3 страницы)")
    print("2. Очистить базу и собрать 1 роль (тест)")
    print("3. Добавить данные без очистки (5 ролей, Москва)")
    print("4. Выход")
    print()
    
    choice = input("Ваш выбор: ").strip()
    
    if choice == '1':
        logger.info("Очистка и полный парсинг...")
        refresh_data(clear=True, roles=list(IT_ROLES.keys())[:10], cities=['Москва'], pages=3)
        
    elif choice == '2':
        logger.info("Тестовый парсинг...")
        refresh_data(clear=True, roles=['python_developer'], cities=['Москва'], pages=2)
        
    elif choice == '3':
        logger.info("Добавление данных...")
        refresh_data(clear=False, roles=list(IT_ROLES.keys())[:5], cities=['Москва'], pages=2)
        
    elif choice == '4':
        sys.exit(0)
        
    else:
        print("Неверный выбор!")
        sys.exit(1)
    
    print()
    print("Готово!")
