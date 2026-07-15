@echo off
:: Сохраняем путь к папке, из которой пользователь ЗАПУСТИЛ команду в консоли
set CURRENT_WORKING_DIR=%cd%

:: Переключаем переменную окружения Python, чтобы он видел наш пакет fastapi_builder_core
set PYTHONPATH=I:\Front\Fastapi;%PYTHONPATH%

:: Запускаем скрипт, передавая ему путь, где нужно создавать файлы app/
python -m fastapi_builder_core.main "%CURRENT_WORKING_DIR%"
