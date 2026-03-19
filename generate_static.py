"""
Скрипт для генерации статической версии сайта для GitHub Pages
"""
import os
import shutil
from datetime import datetime

# Чтение оригинального HTML
with open('templates/index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Замена API вызовов на моковые данные
mock_script = """
<script>
    // Моковые данные для демонстрации
    const MOCK_DATA = {
        status: {
            total_vacancies: 411,
            roles_count: 10,
            cities: ['Москва', 'Санкт-Петербург', 'Екатеринбург', 'Казань'],
            last_updated: '2026-03-19T16:47:01'
        },
        statistics: {
            overall: {
                count: 411,
                min: 80000,
                p25: 120000,
                median: 180000,
                p75: 280000,
                max: 500000,
                average: 195000
            },
            changes: {
                median: 5.2,
                average: 3.8,
                p25: 2.1,
                p75: 7.5,
                count: 15.3
            }
        },
        market: {
            vacancies: { count: 411 },
            resumes: { count: 1250 },
            ratio: 3.04
        }
    };

    // Переопределение fetch для использования моковых данных
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        const mockResponses = {
            '/api/status': JSON.stringify(MOCK_DATA.status),
            '/api/statistics': JSON.stringify({
                overall: MOCK_DATA.statistics.overall,
                changes: MOCK_DATA.statistics.changes,
                by_level: {},
                by_city: {}
            }),
            '/api/market/overview': JSON.stringify(MOCK_DATA.market),
            '/api/years': JSON.stringify([2025, 2026]),
            '/api/roles': JSON.stringify({
                categories: {
                    development: [
                        {id: 'python_developer', name: 'Python разработчик', category: 'development'},
                        {id: 'java_spring_developer', name: 'Java Spring разработчик', category: 'development'}
                    ]
                }
            })
        };

        const urlPath = url.includes('?') ? url.split('?')[0] : url;
        
        if (mockResponses[urlPath]) {
            return Promise.resolve({
                json: () => Promise.resolve(JSON.parse(mockResponses[urlPath])),
                status: 200,
                ok: true
            });
        }

        return originalFetch(url, options);
    };

    // Сообщение о демо-режиме
    console.log('🎭 Демо-режим: используются моковые данные');
</script>
"""

# Вставка мокового скрипта перед закрывающим тегом body
html_content = html_content.replace('</body>', mock_script + '</body>')

# Добавление баннера о демо-режиме
banner_html = """
<div id="demo-banner" style="
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(90deg, #FF6600, #E30611);
    color: white;
    text-align: center;
    padding: 12px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    z-index: 10000;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
">
    🎭 ДЕМО-РЕЖИМ: Показаны примерные данные. Для работы с реальными данными запустите локальную версию.
    <a href="https://github.com/solnce18251/-2.0" target="_blank" style="color: white; margin-left: 10px; text-decoration: underline;">
        📦 GitHub
    </a>
</div>
"""

html_content = html_content.replace('<body>', '<body>' + banner_html)

# Сохранение в папку docs
os.makedirs('docs', exist_ok=True)

with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ Статическая версия сайта создана!")
print(f"📁 Файл: {os.path.abspath('docs/index.html')}")
print()
print("📤 Для публикации на GitHub Pages:")
print("1. Закоммитьте изменения: git add docs & git commit -m 'docs: add static version'")
print("2. Включите Pages в настройках репозитория")
print("3. Выберите branch: main, folder: /docs")
print()
print("🌐 Ссылка будет: https://solnce18251.github.io/-2.0/")
