# Базовый образ
FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /app

COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . ./admin

ENV PYTHONPATH="/app"

# Запускаем приложение
CMD ["python", "admin/main.py"]