# alembic/env.py  (نمونه)
from logging.config import fileConfig
import os
from sqlalchemy import pool
from sqlalchemy.engine import create_engine
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Import your models' MetaData object here
from services.database import Base
target_metadata = Base.metadata

# Use DATABASE_URL env var (sync engine) for Alembic autogenerate to work.
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./data/bot_dev.db")
config.set_main_option("sqlalchemy.url", DB_URL)

def run_migrations_offline():
    context.configure(url=DB_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = create_engine(DB_URL)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
