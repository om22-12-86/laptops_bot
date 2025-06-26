from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from database.database import DATABASE_URL
from database.models import Base  # Импортируем модели для автогенерации миграций

# Загружаем конфигурацию Alembic
config = context.config

# Настройка логирования, если указан конфиг
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Используем метаданные моделей для миграций
target_metadata = Base.metadata

# Создаём синхронный URL для Alembic (меняем postgresql+asyncpg на postgresql)
sync_database_url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

def run_migrations_offline() -> None:
    """Запуск миграций в оффлайн-режиме."""
    context.configure(
        url=sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Запуск миграций в онлайн-режиме."""
    connectable = create_engine(sync_database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
