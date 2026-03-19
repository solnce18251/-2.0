"""
Конфигурация парсера IT-зарплат
"""
import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///salary_data.db')

# Настройки сервера
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Настройки парсинга
PARSER_INTERVAL_HOURS = int(os.getenv('PARSER_INTERVAL_HOURS', 24))
MAX_PAGES_PER_SOURCE = int(os.getenv('MAX_PAGES_PER_SOURCE', 10))
REQUEST_DELAY_SECONDS = int(os.getenv('REQUEST_DELAY_SECONDS', 2))

# Города
CITIES = os.getenv('CITIES', 'Москва,Санкт-Петербург,Екатеринбург,Новосибирск,Казань').split(',')


class Level(Enum):
    """Уровни специалистов"""
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    TEAM_LEAD = "team_lead"


class Category(Enum):
    """Категории IT-ролей"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    DESIGN = "design"
    ENGINEERING = "engineering"
    PROJECT_MANAGEMENT = "project_management"
    ANALYSIS = "analysis"
    ARCHITECTURE = "architecture"


# Список IT-ролей с категориями
IT_ROLES = {
    # Разработка
    "android_developer": {"name": "Android разработчик", "category": Category.DEVELOPMENT},
    "angular_developer": {"name": "Angular разработчик", "category": Category.DEVELOPMENT},
    "csharp_developer": {"name": "C# разработчик", "category": Category.DEVELOPMENT},
    "devops": {"name": "DevOps", "category": Category.DEVELOPMENT},
    "flutter_developer": {"name": "Flutter разработчик", "category": Category.DEVELOPMENT},
    "golang_developer": {"name": "Golang разработчик", "category": Category.DEVELOPMENT},
    "database_developer": {"name": "Разработчик БД", "category": Category.DEVELOPMENT},
    "ios_developer": {"name": "iOS разработчик", "category": Category.DEVELOPMENT},
    "java_spring_developer": {"name": "Java Spring разработчик", "category": Category.DEVELOPMENT},
    "kotlin_developer": {"name": "Kotlin разработчик", "category": Category.DEVELOPMENT},
    "nodejs_developer": {"name": "Node.js разработчик", "category": Category.DEVELOPMENT},
    "php_developer": {"name": "PHP разработчик", "category": Category.DEVELOPMENT},
    "plsql_developer": {"name": "PL/SQL разработчик", "category": Category.DEVELOPMENT},
    "python_developer": {"name": "Python разработчик", "category": Category.DEVELOPMENT},
    "react_developer": {"name": "React разработчик", "category": Category.DEVELOPMENT},
    "ruby_developer": {"name": "Ruby разработчик", "category": Category.DEVELOPMENT},
    "vuejs_developer": {"name": "Vue.js разработчик", "category": Category.DEVELOPMENT},
    "cpp_developer": {"name": "C++ разработчик", "category": Category.DEVELOPMENT},
    "delphi_developer": {"name": "Delphi разработчик", "category": Category.DEVELOPMENT},
    
    # Тестирование
    "qa_engineer": {"name": "Специалист по тестированию", "category": Category.TESTING},
    "qa_mobile": {"name": "Специалист по тестированию Mobile", "category": Category.TESTING},
    "qa_automation": {"name": "Специалист по тестированию Автотесты", "category": Category.TESTING},
    
    # Дизайн
    "ui_ux_designer": {"name": "UI/UX дизайнер", "category": Category.DESIGN},
    
    # Инженеры
    "dba_oracle": {"name": "Администратор БД (Oracle)", "category": Category.ENGINEERING},
    "dba_linux_sip": {"name": "Администратор БД (Linux), SIP", "category": Category.ENGINEERING},
    "system_admin": {"name": "Системный администратор", "category": Category.ENGINEERING},
    "tech_support_2_3": {"name": "Техническая поддержка (2 и 3 линия)", "category": Category.ENGINEERING},
    
    # Управление проектами
    "project_admin": {"name": "Администратор проекта ИТ", "category": Category.PROJECT_MANAGEMENT},
    "project_manager": {"name": "Руководитель проекта", "category": Category.PROJECT_MANAGEMENT},
    "scrum_master": {"name": "Скрам мастер", "category": Category.PROJECT_MANAGEMENT},
    "product_owner": {"name": "Продуктолог (Product Owner)", "category": Category.PROJECT_MANAGEMENT},
    
    # Анализ
    "data_analyst_sql": {"name": "Аналитик данных (SQL)", "category": Category.ANALYSIS},
    "business_analyst": {"name": "Бизнес аналитик", "category": Category.ANALYSIS},
    "system_analyst": {"name": "Системный аналитик", "category": Category.ANALYSIS},
    "technical_writer": {"name": "Технический писатель", "category": Category.ANALYSIS},
    
    # Архитектура
    "system_architect": {"name": "Системный архитектор", "category": Category.ARCHITECTURE},
}

# Ключевые слова для определения уровня по описанию вакансии
LEVEL_KEYWORDS = {
    Level.JUNIOR: ["junior", "jun", "начинающий", "стажер", "trainee", "без опыта", "до 2 лет"],
    Level.MIDDLE: ["middle", "mid", "средний", "от 2 лет", "от 3 лет", "2-4 года"],
    Level.SENIOR: ["senior", "sr", "старший", "от 5 лет", "ведущий", "lead"],
    Level.TEAM_LEAD: ["team lead", "teamlead", "руководитель команды", "head of", "управление командой"],
}

# Ключевые слова для определения роли по названию вакансии
ROLE_KEYWORDS = {
    "android_developer": ["android", "андроид", "kotlin", "java android"],
    "angular_developer": ["angular", "ангуляр"],
    "csharp_developer": ["c#", "c sharp", "dotnet", ".net"],
    "devops": ["devops", "девопс", "ci/cd", "kubernetes", "docker"],
    "flutter_developer": ["flutter", "флаттер", "dart"],
    "golang_developer": ["golang", "go", "го"],
    "database_developer": ["sql разработчик", "разработчик бд", "pl/sql"],
    "ios_developer": ["ios", "iphone", "swift", "objective-c"],
    "java_spring_developer": ["java", "spring", "джава"],
    "kotlin_developer": ["kotlin", "котлин"],
    "nodejs_developer": ["node.js", "nodejs", "node js"],
    "php_developer": ["php", "пхп", "laravel", "symfony"],
    "plsql_developer": ["pl/sql", "plsql", "oracle pl/sql"],
    "python_developer": ["python", "питон", "django", "flask", "fastapi"],
    "react_developer": ["react", "реакт", "react.js", "redux"],
    "ruby_developer": ["ruby", "руби", "rails", "ruby on rails"],
    "vuejs_developer": ["vue.js", "vuejs", "vue", "виву"],
    "cpp_developer": ["c++", "cpp", "си++"],
    "delphi_developer": ["delphi", "делфи", "pascal"],
    "qa_engineer": ["тестировщик", "qa", "ручное тестирование", "manual"],
    "qa_mobile": ["mobile qa", "мобильное тестирование", "qa mobile"],
    "qa_automation": ["автотесты", "automation", "selenium", "pytest", "автоматизация"],
    "ui_ux_designer": ["ui/ux", "ui ux", "ux/ui", "дизайнер интерфейсов", "product designer"],
    "dba_oracle": ["dba oracle", "администратор oracle"],
    "dba_linux_sip": ["sip", "linux администратор", "voip"],
    "system_admin": ["системный администратор", "сисадмин", "system administrator"],
    "tech_support_2_3": ["техническая поддержка", "support", "helpdesk", "2 линия", "3 линия"],
    "project_admin": ["администратор проекта", "project coordinator"],
    "project_manager": ["project manager", "руководитель проекта", "менеджер проекта"],
    "scrum_master": ["scrum master", "скрам мастер"],
    "product_owner": ["product owner", "продуктовый владелец", "продакт оунер"],
    "data_analyst_sql": ["data analyst", "аналитик данных", "sql analyst"],
    "business_analyst": ["business analyst", "бизнес аналитик", "ba"],
    "system_analyst": ["system analyst", "системный аналитик", "са"],
    "technical_writer": ["technical writer", "технический писатель", "документация"],
    "system_architect": ["system architect", "системный архитектор", "архитектор по"],
}


def get_role_by_keywords(title: str) -> str | None:
    """Определить роль по ключевым словам в названии"""
    title_lower = title.lower()
    for role_id, keywords in ROLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title_lower:
                return role_id
    return None


def get_level_by_keywords(title: str, experience: str = "") -> Level:
    """Определить уровень по ключевым словам"""
    text = f"{title} {experience}".lower()
    
    # Сначала проверяем Team Lead
    for keyword in LEVEL_KEYWORDS[Level.TEAM_LEAD]:
        if keyword in text:
            return Level.TEAM_LEAD
    
    # Затем Senior
    for keyword in LEVEL_KEYWORDS[Level.SENIOR]:
        if keyword in text:
            return Level.SENIOR
    
    # Затем Middle
    for keyword in LEVEL_KEYWORDS[Level.MIDDLE]:
        if keyword in text:
            return Level.MIDDLE
    
    # По умолчанию Junior
    return Level.JUNIOR
