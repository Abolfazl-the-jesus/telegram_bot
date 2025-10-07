from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import create_engine, pool

# Import your models' MetaData object here
from services.database import Base

# Alembic Config
config = context.config

# Configure Python logging from the alembic.ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for 'autogenerate'
target_metadata = Base.metadata

# Use DATABASE_URL env var for Alembic autogenerate to work (sync engine)
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./data/bot_dev.db")
config.set_main_option("sqlalchemy.url", DB_URL)


def run_migrations_offline():
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(DB_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

*** Begin Patch
@@
from sqlalchemy import pool
from sqlalchemy.engine import create_engine
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import pool
from sqlalchemy.engine import create_engine
from sqlalchemy import engine_from_config
from sqlalchemy import pool
@@
from services.database import Base
from services.database import Base
*** End Patchle for Python logging.
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
