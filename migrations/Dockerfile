FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

ENV PYTHONPATH="/app"

CMD ["bash", "-c", "alembic revision --autogenerate -m 'auto migration' || true && alembic upgrade head"]
