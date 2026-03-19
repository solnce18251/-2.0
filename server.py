"""
Веб-сервер с API для доступа к данным о зарплатах
"""
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from config import IT_ROLES, Category, Level, CITIES, HOST, PORT, DEBUG
from database import Database
from models.market import Resume
from parsers.data_collector import DataCollector
from parsers.hh_resume_parser import HHResumeParser
import os
import pandas as pd
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Конфигурация для загрузки файлов
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

# Инициализация базы данных
db = Database()

# Создание папки для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Проверка расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Главная страница с дашбордом"""
    return render_template('index.html')


@app.route('/api/roles')
def get_roles():
    """Получение списка всех ролей"""
    roles = []
    for role_id, role_info in IT_ROLES.items():
        roles.append({
            'id': role_id,
            'name': role_info['name'],
            'category': role_info['category'].value,
        })
    
    # Группировка по категориям
    categories = {}
    for role in roles:
        cat = role['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(role)
    
    return jsonify({
        'roles': roles,
        'categories': categories
    })


@app.route('/api/levels')
def get_levels():
    """Получение списка уровней"""
    levels = [
        {'id': Level.JUNIOR.value, 'name': 'Junior (до 2 лет)', 'description': 'Опыт работы до 2 лет'},
        {'id': Level.MIDDLE.value, 'name': 'Middle (2-4 года)', 'description': 'Опыт работы от 2 до 4 лет'},
        {'id': Level.SENIOR.value, 'name': 'Senior (от 5 лет)', 'description': 'Опыт работы от 5 лет'},
        {'id': Level.TEAM_LEAD.value, 'name': 'Team Lead', 'description': 'Опыт от 5 лет + управление командой'},
    ]
    return jsonify(levels)


@app.route('/api/cities')
def get_cities():
    """Получение списка городов"""
    # Добавляем "Россия" как общий вариант
    cities_list = ['Россия'] + list(CITIES)
    return jsonify(cities_list)


@app.route('/api/years')
def get_years():
    """Получение списка годов, за которые есть данные"""
    years = db.get_years_with_data()
    return jsonify(years)


@app.route('/api/market/overview')
def get_market_overview():
    """
    Получение обзора рынка: вакансии + резюме

    Параметры:
    - role_ids: список ID ролей
    - levels: список уровней
    - cities: список городов
    - date_from: дата начала периода
    - date_to: дата окончания периода
    """
    try:
        role_ids = request.args.get('role_ids', '')
        role_ids = [r.strip() for r in role_ids.split(',') if r.strip()] if role_ids else None

        levels = request.args.get('levels', '')
        levels = [l.strip() for l in levels.split(',') if l.strip()] if levels else None

        cities = request.args.get('cities', '')
        cities = [c.strip() for c in cities.split(',') if c.strip()] if cities else None

        date_from_str = request.args.get('date_from', '')
        date_to_str = request.args.get('date_to', '')

        date_from = None
        date_to = None

        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            except ValueError:
                pass

        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
                date_to = date_to.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass

        overview = db.get_market_overview(
            role_ids=role_ids,
            levels=levels,
            cities=cities,
            date_from=date_from,
            date_to=date_to
        )

        return jsonify(overview)

    except Exception as e:
        logger.error(f"Ошибка получения обзора рынка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/market/resumes')
def get_resumes_stats():
    """
    Статистика по резюме

    Параметры:
    - role_ids: список ID ролей
    - levels: список уровней
    - cities: список городов
    - date_from: дата начала периода
    - date_to: дата окончания периода
    """
    try:
        role_ids = request.args.get('role_ids', '')
        role_ids = [r.strip() for r in role_ids.split(',') if r.strip()] if role_ids else None

        levels = request.args.get('levels', '')
        levels = [l.strip() for l in levels.split(',') if l.strip()] if levels else None

        cities = request.args.get('cities', '')
        cities = [c.strip() for c in cities.split(',') if c.strip()] if cities else None

        date_from_str = request.args.get('date_from', '')
        date_to_str = request.args.get('date_to', '')

        date_from = None
        date_to = None

        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            except ValueError:
                pass

        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
                date_to = date_to.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass

        stats = db.get_resume_statistics(
            role_ids=role_ids,
            levels=levels,
            cities=cities,
            date_from=date_from,
            date_to=date_to
        )

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Ошибка получения статистики резюме: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/parse-resumes', methods=['POST'])
def parse_resumes():
    """Запуск парсинга резюме"""
    try:
        data = request.get_json() or {}

        role_ids = data.get('role_ids', None)
        cities = data.get('cities', CITIES[:3])
        pages = data.get('pages', 3)

        if not role_ids:
            role_ids = list(IT_ROLES.keys())[:5]  # По умолчанию первые 5 ролей

        collected = 0

        parser = HHResumeParser(delay=1.5)

        for role_id in role_ids:
            for city in cities:
                resumes = parser.parse_resumes(
                    role_id=role_id,
                    city=city,
                    pages=pages
                )

                if resumes:
                    added = db.add_resumes_batch(resumes)
                    collected += added

        parser.close()

        return jsonify({
            'success': True,
            'collected': collected,
            'message': f'Собрано {collected} резюме'
        })

    except Exception as e:
        logger.error(f"Ошибка парсинга резюме: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/import-resumes', methods=['POST'])
def import_resumes():
    """
    Импорт резюме из Excel/CSV файла
    
    Формат данных:
    - Файл: .xlsx, .xls, .csv
    - Колонки: Должность, Зарплата от, Зарплата до, Город, Опыт работы, Уровень, Навыки, Дата публикации
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Allowed: xlsx, xls, csv'}), 400
        
        # Сохранение файла
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Чтение файла
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        logger.info(f"Загружено {len(df)} строк из файла {filename}")
        
        # Импорт в базу
        from import_resumes import map_role_id, map_level, parse_date
        
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
                    source='hr_analyst_import',
                    url=str(row.get('Ссылка', row.get('URL', ''))),
                    published_at=parse_date(row.get('Дата публикации', row.get('Date', ''))),
                    updated_at=datetime.utcnow(),
                )
                
                db.add_resumes_batch([resume])  # Используем метод для резюме
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка при импорте строки {idx}: {e}")
                continue
        
        # Удаление файла после импорта
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'imported': imported_count,
            'total': len(df),
            'message': f'Импортировано {imported_count} из {len(df)} резюме'
        })
        
    except Exception as e:
        logger.error(f"Ошибка импорта: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Получение статистики по зарплатам

    Параметры:
    - role_ids: список ID ролей (через запятую)
    - levels: список уровней (через запятую)
    - cities: список городов (через запятую)
    - date_from: дата начала периода (YYYY-MM-DD)
    - date_to: дата окончания периода (YYYY-MM-DD)
    """
    try:
        # Парсинг параметров
        role_ids = request.args.get('role_ids', '')
        role_ids = [r.strip() for r in role_ids.split(',') if r.strip()] if role_ids else None

        levels = request.args.get('levels', '')
        levels = [l.strip() for l in levels.split(',') if l.strip()] if levels else None

        cities = request.args.get('cities', '')
        cities = [c.strip() for c in cities.split(',') if c.strip()] if cities else None

        # Обработка фильтра "Регионы" (все города кроме Москвы)
        if cities and 'Регионы' in cities:
            from config import CITIES
            # Для регионов берем все города из базы кроме Москвы
            cities = [c for c in CITIES if c != 'Москва']
            # Добавляем "Россия" как общий вариант
            if 'Россия' not in cities:
                cities.append('Россия')

        # Обработка дат из календаря
        date_from = None
        date_to = None

        date_from_str = request.args.get('date_from', '')
        date_to_str = request.args.get('date_to', '')

        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            except ValueError:
                pass

        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
                # Устанавливаем конец дня
                date_to = date_to.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass

        # Получение статистики
        stats = db.get_salary_statistics(
            role_ids=role_ids,
            levels=levels,
            cities=cities,
            date_from=date_from,
            date_to=date_to
        )
        
        # Получение данных для графика по уровням
        level_stats = {}
        if role_ids:
            for level in [Level.JUNIOR.value, Level.MIDDLE.value, Level.SENIOR.value, Level.TEAM_LEAD.value]:
                level_stat = db.get_salary_statistics(
                    role_ids=role_ids,
                    levels=[level],
                    cities=cities,
                    date_from=date_from
                )
                if level_stat.get('count', 0) > 0:
                    level_stats[level] = level_stat
        
        # Получение данных по городам
        city_stats = {}
        if cities and len(cities) > 1:
            for city in cities:
                city_stat = db.get_salary_statistics(
                    role_ids=role_ids,
                    levels=levels,
                    cities=[city],
                    date_from=date_from,
                    date_to=date_to
                )
                if city_stat.get('count', 0) > 0:
                    city_stats[city] = city_stat

        # Получение данных за предыдущий период для сравнения
        prev_stats = {}
        if date_from and date_to:
            period_days = (date_to - date_from).days + 1
            prev_date_from = date_from - timedelta(days=period_days)
            prev_date_to = date_from - timedelta(days=1)
            
            prev_stats = db.get_salary_statistics(
                role_ids=role_ids,
                levels=levels,
                cities=cities,
                date_from=prev_date_from,
                date_to=prev_date_to
            )
        elif date_from:
            # Если только date_from, берём такой же период до
            period_days = 30  # По умолчанию 30 дней
            prev_date_from = date_from - timedelta(days=period_days)
            prev_date_to = date_from - timedelta(days=1)
            
            prev_stats = db.get_salary_statistics(
                role_ids=role_ids,
                levels=levels,
                cities=cities,
                date_from=prev_date_from,
                date_to=prev_date_to
            )

        # Расчёт изменений в процентах
        changes = {}
        if prev_stats.get('count', 0) > 0 and stats.get('count', 0) > 0:
            for key in ['median', 'average', 'p25', 'p75', 'min', 'max']:
                if stats.get(key) and prev_stats.get(key):
                    change = ((stats[key] - prev_stats[key]) / prev_stats[key]) * 100
                    changes[key] = round(change, 2)
        
        # Изменение количества вакансий
        if prev_stats.get('count', 0) > 0:
            change_count = ((stats['count'] - prev_stats['count']) / prev_stats['count']) * 100
            changes['count'] = round(change_count, 2)

        return jsonify({
            'overall': stats,
            'previous_period': prev_stats,
            'changes': changes,
            'by_level': level_stats,
            'by_city': city_stats,
            'filters': {
                'role_ids': role_ids,
                'levels': levels,
                'cities': cities,
                'date_from': date_from_str if date_from_str else None,
                'date_to': date_to_str if date_to_str else None,
            }
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics/roles-compare')
def compare_roles():
    """Сравнение зарплат по разным ролям"""
    try:
        levels = request.args.get('levels', '')
        levels = [l.strip() for l in levels.split(',') if l.strip()] if levels else None

        cities = request.args.get('cities', '')
        cities = [c.strip() for c in cities.split(',') if c.strip()] if cities else None

        # Обработка дат из календаря
        date_from = None
        date_to = None
        
        date_from_str = request.args.get('date_from', '')
        date_to_str = request.args.get('date_to', '')
        
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
                date_to = date_to.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass

        # Статистика по каждой роли
        roles_data = {}
        for role_id in IT_ROLES.keys():
            stat = db.get_salary_statistics(
                role_ids=[role_id],
                levels=levels,
                cities=cities,
                date_from=date_from,
                date_to=date_to
            )
            if stat.get('count', 0) > 0:
                roles_data[role_id] = {
                    'name': IT_ROLES[role_id]['name'],
                    'category': IT_ROLES[role_id]['category'].value,
                    **stat
                }

        return jsonify(roles_data)

    except Exception as e:
        logger.error(f"Ошибка сравнения ролей: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics/trend')
def get_trend():
    """Получение тренда зарплат по времени"""
    try:
        role_ids = request.args.get('role_ids', '')
        role_ids = [r.strip() for r in role_ids.split(',') if r.strip()] if role_ids else None

        levels = request.args.get('levels', '')
        levels = [l.strip() for l in levels.split(',') if l.strip()] if levels else None

        cities = request.args.get('cities', '')
        cities = [c.strip() for c in cities.split(',') if c.strip()] if cities else None

        # Обработка дат из календаря
        date_from_param = None
        date_to_param = None
        
        date_from_str = request.args.get('date_from', '')
        date_to_str = request.args.get('date_to', '')
        
        if date_from_str:
            try:
                date_from_param = datetime.strptime(date_from_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        if date_to_str:
            try:
                date_to_param = datetime.strptime(date_to_str, '%Y-%m-%d')
                date_to_param = date_to_param.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass

        # Если даты не указаны, используем последние 12 месяцев
        if date_from_param and date_to_param:
            # Вычисляем количество месяцев между датами
            months_diff = (date_to_param.year - date_from_param.year) * 12 + (date_to_param.month - date_from_param.month)
            months = max(1, min(months_diff + 1, 24))  # От 1 до 24 месяцев
            
            # Начинаем с месяца даты начала
            current_date = date_from_param.replace(day=1)
            trend_data = []
            
            for i in range(months):
                next_month = current_date.replace(month=current_date.month % 12 + 1) if current_date.month < 12 else current_date.replace(year=current_date.year + 1, month=1)
                if i == months - 1 and date_to_param:
                    month_end = date_to_param
                else:
                    month_end = next_month - timedelta(days=1)
                
                month_label = current_date.strftime('%Y-%m')
                
                stat = db.get_salary_statistics(
                    role_ids=role_ids,
                    levels=levels,
                    cities=cities,
                    date_from=current_date,
                    date_to=month_end
                )
                
                trend_data.append({
                    'month': month_label,
                    **stat
                })
                
                current_date = next_month
        else:
            # Группировка по месяцам за последний год (по умолчанию)
            months = 12
            trend_data = []

            for i in range(months, 0, -1):
                date_from = datetime.utcnow() - timedelta(days=30 * i)
                date_to = datetime.utcnow() - timedelta(days=30 * (i - 1))

                month_label = date_from.strftime('%Y-%m')

                stat = db.get_salary_statistics(
                    role_ids=role_ids,
                    levels=levels,
                    cities=cities,
                    date_from=date_from,
                    date_to=date_to
                )

                trend_data.append({
                    'month': month_label,
                    **stat
                })

        return jsonify(trend_data)

    except Exception as e:
        logger.error(f"Ошибка получения тренда: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/parse', methods=['POST'])
def start_parsing():
    """Запуск парсинга данных"""
    try:
        data = request.get_json() or {}
        
        role_ids = data.get('role_ids', None)
        cities = data.get('cities', CITIES[:3])
        sources = data.get('sources', ['hh', 'habr'])
        pages = data.get('pages', 3)
        
        # Если role_ids не указан, парсим все роли
        if not role_ids:
            role_ids = list(IT_ROLES.keys())
        
        collected = 0
        
        with DataCollector() as collector:
            for role_id in role_ids:
                for city in cities:
                    vacancies = collector.collect_for_role(
                        role_id=role_id,
                        city=city,
                        sources=sources,
                        pages_per_source=pages
                    )
                    
                    # Сохранение в базу
                    if vacancies:
                        db_vacancies = [Vacancy.from_parser_data(v) for v in vacancies]
                        collected += db.add_vacancies_batch(db_vacancies)
        
        return jsonify({
            'success': True,
            'collected': collected,
            'message': f'Собрано {collected} вакансий'
        })
        
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status')
def get_status():
    """Получение статуса базы данных"""
    from models.vacancy import Vacancy
    
    total = db.get_vacancy_count()
    min_date, max_date = db.get_date_range()
    roles = db.get_all_roles_with_data()
    cities = db.get_all_cities_with_data()
    
    return jsonify({
        'total_vacancies': total,
        'date_range': {
            'min': min_date.isoformat() if min_date else None,
            'max': max_date.isoformat() if max_date else None,
        },
        'roles_count': len(roles),
        'cities': cities,
        'last_updated': max_date.isoformat() if max_date else None,
    })


# Импорт Vacancy для использования в server.py
from models.vacancy import Vacancy


if __name__ == '__main__':
    logger.info(f"Запуск сервера на {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
