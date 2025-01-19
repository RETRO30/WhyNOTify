# Базовый образ
FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /notifications

COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . ./notifications

# Запускаем приложение
CMD ["python", "notifications/main.py"]
