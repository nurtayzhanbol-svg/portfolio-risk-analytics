import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://portfolio:portfolio@localhost:5432/portfolio")
