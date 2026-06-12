from logging.config import fileConfig
import os
import sys
from pathlib import Path

# Ensure backend root is on Python import path for alembic runtime
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.append(str(ROOT))

from alembic import context
from app.db import Base, engine
import app.models.user
import app.models.business
import app.models.vehicle
import app.models.workorder
import app.models.review
import app.models.service
import app.models.business_service

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be set for offline migrations")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
