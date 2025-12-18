# Використовуємо легкий образ Python
FROM python:3.11-slim

# Встановлюємо змінні оточення для Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Встановлюємо робочу директорію
WORKDIR /app

# 1. Встановлюємо системні залежності та PostgreSQL Client
# Додаємо --fix-missing для стабільності
RUN apt-get update --fix-missing && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 2. Встановлюємо Google Chrome (НОВИЙ МЕТОД: через .deb файл)
# Цей метод не потребує apt-key і працює на Debian 12
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 3. Копіюємо файл із залежностями
COPY requirements.txt .

# 4. Встановлюємо Python-бібліотеки
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копіюємо весь код проєкту в контейнер
COPY . .

# 6. Запускаємо main.py
CMD ["python", "main.py"]
