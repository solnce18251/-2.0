# 🔄 Обновление данных парсера

## Почему данные устарели?

В базе данных сейчас **6426 вакансий** с датой от **декабря 2025**. Это связано с тем, что:

1. **Парсинг не запускался автоматически** — нужно запускать вручную
2. **Проверка на дубликаты** — предотвращает повторное добавление тех же вакансий по URL
3. **Данные устаревают** — вакансии закрываются, появляются новые

---

## Способы обновления

### Способ 1: Скрипт обновления (рекомендуется)

```bash
cd "c:\Users\solnc\Desktop\Парсер 2.0"
python refresh_data.py
```

**Варианты:**
1. Очистить базу и собрать заново (10 ролей, Москва, 3 страницы)
2. Очистить базу и собрать 1 роль (тест)
3. Добавить данные без очистки (5 ролей, Москва)

### Способ 2: Через консоль

```bash
cd "c:\Users\solnc\Desktop\Парсер 2.0"
python run.py parse --roles python_developer java_spring_developer --cities Москва --pages 3
```

### Способ 3: Через веб-интерфейс

1. Откройте http://127.0.0.1:5000
2. Нажмите **"🔄 Обновить данные"**
3. Выберите города
4. Нажмите **"Начать парсинг"**

---

## Автоматическое обновление

### Настройка по расписанию (Windows Task Scheduler)

1. Откройте **Task Scheduler**
2. **Create Basic Task**
3. Name: "IT Salary Parser Update"
4. Trigger: **Daily** (ежедневно в 00:00)
5. Action: **Start a program**
   - Program: `python.exe`
   - Arguments: `refresh_data.py`
   - Start in: `c:\Users\solnc\Desktop\Парсер 2.0`

### Через Python (schedule library)

```python
# scheduler.py
import schedule
import time
from refresh_data import refresh_data

def job():
    refresh_data(clear=False, roles=None, cities=['Москва'], pages=2)

schedule.every().day.at("00:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Очистка старых данных

### Удалить данные старше 30 дней:
```bash
python -c "from refresh_data import clear_old_data; clear_old_data(30)"
```

### Удалить ВСЕ данные:
```bash
python -c "from refresh_data import clear_old_data; clear_old_data(0)"
```

---

## Проверка данных

### Через консоль:
```bash
python -c "
from database import Database
db = Database()
print(f'Вакансий: {db.get_vacancy_count()}')
min_date, max_date = db.get_date_range()
print(f'Диапазон дат: {min_date} - {max_date}')
"
```

### Через API:
```bash
curl http://127.0.0.1:5000/api/status
```

---

## Рекомендации

### Для актуальных данных:

1. **Запускайте парсинг ежедневно** (ночью)
2. **Очищайте данные раз в неделю** (удаляйте закрытые вакансии)
3. **Парсите топ-10 ролей** по 2-3 страницы
4. **Используйте несколько городов** (Москва + СПб)

### Пример ежедневного обновления:

```bash
# Очистка данных старше 7 дней
python -c "from refresh_data import clear_old_data; clear_old_data(7)"

# Парсинг новых данных
python run.py parse --roles python_developer java_spring_developer react_developer --cities Москва Санкт-Петербург --pages 3
```

---

## Проблемы и решения

### Парсинг не добавляет данные

**Проблема:** Проверка на дубликаты по URL

**Решение:**
```bash
# Очистить базу
python -c "from refresh_data import clear_old_data; clear_old_data(0)"

# Запустить парсинг заново
python refresh_data.py
```

### Парсинг работает медленно

**Проблема:** Задержки между запросами

**Решение:** Уменьшите задержку в `parsers/hh_parser.py`:
```python
def __init__(self, delay: float = 0.5):  # Было 1.0
    super().__init__(delay=delay)
```

### API hh.ru не отвечает

**Проблема:** Блокировка по IP или лимиты

**Решение:**
1. Увеличьте задержку между запросами
2. Используйте прокси
3. Парсите по 1-2 роли за раз

---

## Статистика

| Действие | Время | Результат |
|----------|-------|-----------|
| Парсинг 1 роли (3 стр) | 2-3 мин | ~100-300 вакансий |
| Парсинг 10 ролей (3 стр) | 20-30 мин | ~1000-3000 вакансий |
| Очистка базы | 5-10 сек | Все данные удалены |

---

## Контакты

Вопросы? Создайте issue в GitHub репозитории.
