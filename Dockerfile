# Використовуємо стабільну версію Bullseye (важливо для Docker Toolbox)
FROM python:3.11-slim-bullseye

# Встановлюємо змінні оточення
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Робоча директорія
WORKDIR /app

# 1. Встановлюємо системні залежності
# Використовуємо --no-install-recommends для зменшення сміття
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 2. Копіюємо файл залежностей
COPY requirements.txt .

# 3. Встановлюємо бібліотеки
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копіюємо код
COPY . .

# 5. Запуск
CMD ["python", "main.py"]
