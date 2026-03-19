"""
IT Salary Parser - Главный скрипт запуска
"""
import argparse
import logging
import sys
from datetime import datetime

from config import IT_ROLES, CITIES
from database import Database
from parsers.data_collector import DataCollector
from models.vacancy import Vacancy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_all(roles: list = None, cities: list = None, pages: int = 3):
    """
    Парсинг всех вакансий
    
    Args:
        roles: Список ID ролей для парсинга
        cities: Список городов
        pages: Количество страниц для каждого источника
    """
    if roles is None:
        roles = list(IT_ROLES.keys())
    
    if cities is None:
        cities = CITIES[:3]  # По умолчанию первые 3 города
    
    logger.info(f"Начало парсинга: {len(roles)} ролей, города: {cities}")
    
    db = Database()
    
    with DataCollector() as collector:
        total_collected = 0
        
        for role_id in roles:
            role_name = IT_ROLES.get(role_id, {}).get('name', role_id)
            logger.info(f"Парсинг роли: {role_name}")
            
            for city in cities:
                logger.info(f"  Город: {city}")
                
                vacancies = collector.collect_for_role(
                    role_id=role_id,
                    city=city,
                    pages_per_source=pages
                )
                
                if vacancies:
                    db_vacancies = [Vacancy.from_parser_data(v) for v in vacancies]
                    added = db.add_vacancies_batch(db_vacancies)
                    total_collected += added
                    logger.info(f"    Добавлено: {added} вакансий")
    
    logger.info(f"Парсинг завершен. Всего добавлено: {total_collected} вакансий")
    db.close()
    
    return total_collected


def parse_role(role_id: str, city: str = 'Москва', pages: int = 5):
    """
    Парсинг конкретной роли
    
    Args:
        role_id: ID роли
        city: Город
        pages: Количество страниц
    """
    if role_id not in IT_ROLES:
        logger.error(f"Неизвестная роль: {role_id}")
        logger.info(f"Доступные роли: {list(IT_ROLES.keys())}")
        return 0
    
    logger.info(f"Парсинг {IT_ROLES[role_id]['name']} в городе {city}")
    
    db = Database()
    
    with DataCollector() as collector:
        vacancies = collector.collect_for_role(
            role_id=role_id,
            city=city,
            pages_per_source=pages
        )
        
        if vacancies:
            db_vacancies = [Vacancy.from_parser_data(v) for v in vacancies]
            added = db.add_vacancies_batch(db_vacancies)
            logger.info(f"Добавлено {added} вакансий")
    
    db.close()
    return added


def run_server(host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    """
    Запуск веб-сервера
    
    Args:
        host: Хост
        port: Порт
        debug: Режим отладки
    """
    from server import app
    logger.info(f"Запуск сервера на {host}:{port}")
    app.run(host=host, port=port, debug=debug)


def show_stats():
    """Показать статистику базы данных"""
    db = Database()
    
    total = db.get_vacancy_count()
    min_date, max_date = db.get_date_range()
    roles = db.get_all_roles_with_data()
    cities = db.get_all_cities_with_data()
    
    print("\n" + "="*50)
    print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ")
    print("="*50)
    print(f"Всего вакансий: {total}")
    print(f"Диапазон дат: {min_date} - {max_date}")
    print(f"Ролей с данными: {len(roles)}")
    print(f"Городов: {len(cities)}")
    
    if roles:
        print("\nРоли:")
        for role in sorted(roles):
            print(f"  - {role}")
    
    if cities:
        print("\nГорода:")
        for city in sorted(cities):
            print(f"  - {city}")
    
    print("="*50 + "\n")
    
    db.close()


def clear_old_data(days: int = 90):
    """
    Очистка старых данных
    
    Args:
        days: Удалять данные старше этого количества дней
    """
    db = Database()
    deleted = db.clear_old_data(days)
    logger.info(f"Удалено {deleted} записей старше {days} дней")
    db.close()


def main():
    parser = argparse.ArgumentParser(
        description='IT Salary Parser - Сбор и анализ зарплатных данных',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python run.py parse                          # Парсинг всех ролей
  python run.py parse --roles python_developer --city Москва
  python run.py server                         # Запуск веб-сервера
  python run.py stats                          # Показать статистику
  python run.py clear --days 30                # Очистить данные старше 30 дней
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда parse
    parse_parser = subparsers.add_parser('parse', help='Запуск парсинга')
    parse_parser.add_argument('--roles', nargs='+', help='ID ролей для парсинга')
    parse_parser.add_argument('--cities', nargs='+', help='Города для парсинга')
    parse_parser.add_argument('--pages', type=int, default=3, help='Количество страниц')
    parse_parser.add_argument('--role', help='Парсить только одну роль')
    parse_parser.add_argument('--city', default='Москва', help='Город для одной роли')
    
    # Команда server
    server_parser = subparsers.add_parser('server', help='Запуск веб-сервера')
    server_parser.add_argument('--host', default='127.0.0.1', help='Хост')
    server_parser.add_argument('--port', type=int, default=5000, help='Порт')
    server_parser.add_argument('--debug', action='store_true', help='Режим отладки')
    
    # Команда stats
    subparsers.add_parser('stats', help='Показать статистику БД')
    
    # Команда clear
    clear_parser = subparsers.add_parser('clear', help='Очистить старые данные')
    clear_parser.add_argument('--days', type=int, default=90, help='Дней')
    
    args = parser.parse_args()
    
    if args.command == 'parse':
        if args.role:
            parse_role(args.role, args.city, args.pages)
        else:
            parse_all(args.roles, args.cities, args.pages)
    
    elif args.command == 'server':
        run_server(args.host, args.port, args.debug)
    
    elif args.command == 'stats':
        show_stats()
    
    elif args.command == 'clear':
        clear_old_data(args.days)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
