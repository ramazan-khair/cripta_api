from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import PostgresConfig


def new_session_maker(psql_config: PostgresConfig) -> async_sessionmaker[AsyncSession]:
    database_uri = f'postgresql+psycopg://{psql_config.login}:{psql_config.password}@{psql_config.host}:{psql_config.port}/{psql_config.database}'

    engine = create_async_engine(
        database_uri,
        pool_size=15,
        max_overflow=5,
        connect_args={
            "connect_timeout": 5,
        }
    )
    return async_sessionmaker(engine, class_=AsyncSession, autoflush=False, expire_on_commit=False)