@echo off
chcp 65001 >nul
echo ============================================
echo    IT Salary Parser 2.0 - Запуск
echo ============================================
echo.

:menu
echo Выберите действие:
echo.
echo 1. Запустить парсинг данных (все роли)
echo 2. Запустить веб-сервер
echo 3. Показать статистику базы
echo 4. Парсинг конкретной роли
echo 5. Очистить старые данные
echo 6. Выйти
echo.
set /p choice="Ваш выбор: "

if "%choice%"=="1" goto parse_all
if "%choice%"=="2" goto server
if "%choice%"=="3" goto stats
if "%choice%"=="4" goto parse_role
if "%choice%"=="5" goto clear
if "%choice%"=="6" goto end

echo Неверный выбор!
goto menu

:parse_all
echo.
echo Запуск парсинга всех ролей...
python run.py parse
echo.
echo Парсинг завершен!
pause
goto menu

:server
echo.
echo Запуск веб-сервера...
echo Откройте в браузере: http://127.0.0.1:5000
echo Нажмите Ctrl+C для остановки сервера
python run.py server --debug
goto menu

:stats
echo.
python run.py stats
pause
goto menu

:parse_role
echo.
set /p role="Введите ID роли (например, python_developer): "
set /p city="Введите город (по умолчанию Москва): "
if "%city%"=="" set city=Москва
python run.py parse --role %role% --city %city%
pause
goto menu

:clear
echo.
set /p days="Введите количество дней (по умолчанию 90): "
if "%days%"=="" set days=90
python run.py clear --days %days%
pause
goto menu

:end
echo.
echo До свидания!
