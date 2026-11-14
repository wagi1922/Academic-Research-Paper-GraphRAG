from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class Neo4jDriver:
    _driver: AsyncDriver | None = None

    @classmethod
    def get_driver(cls) -> AsyncDriver:
        if cls._driver is None:
            cls._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0,
            )
            logger.info(f"Neo4j driver initialized: {settings.neo4j_uri}")
        return cls._driver

    @classmethod
    async def close(cls):
        if cls._driver:
            await cls._driver.close()
            cls._driver = None
            logger.info("Neo4j driver closed")

    @classmethod
    async def verify_connectivity(cls) -> bool:
        try:
            driver = cls.get_driver()
            await driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j connectivity check failed: {e}")
            return False


async def get_session():
    driver = Neo4jDriver.get_driver()
    async with driver.session(database=settings.neo4j_database) as session:
        yield session


# Alias for backward compatibility
get_neo4j_session = get_session


async def close_neo4j_driver():
    """Close the Neo4j driver connection."""
    await Neo4jDriver.close()