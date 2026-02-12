from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:1122@localhost:5432/postgres"

engine = create_engine(DATABASE_URL)
