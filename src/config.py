import os
from dotenv import load_dotenv


load_dotenv()

# Connection string
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "192.168.99.100")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "autoria_db")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# URL for scrape data
BASE_URL = "https://auto.ria.com/uk/car/used/"

# Scrape config
SCRAPE_TIME = os.getenv("SCRAPE_TIME", "12:00")
