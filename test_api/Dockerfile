# Базовый образ
FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
RUN pip install flask

# Копируем код
COPY . ./test_api

ENV PYTHONPATH="/app"

# Запускаем приложение
CMD ["python", "test_api/main.py"]