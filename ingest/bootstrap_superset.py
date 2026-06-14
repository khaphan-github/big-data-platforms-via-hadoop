from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("superset-bootstrap")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(os.getenv("SUPERSET_LOG_LEVEL", "INFO").upper())


@dataclass(frozen=True)
class BootstrapConfig:
    database_name: str
    sqlalchemy_uri: str
    dataset_schema: str
    dataset_table: str
    dataset_label: str


def build_config() -> BootstrapConfig:
    hive_host = os.getenv("HIVE_HOST", "hive-server")
    hive_port = os.getenv("HIVE_PORT", "10000")
    hive_database = os.getenv("HIVE_DATABASE", "rss_analytics")
    hive_table = os.getenv("HIVE_ARTICLES_TABLE", "rss_articles")

    return BootstrapConfig(
        database_name=os.getenv("SUPERSET_DATABASE_NAME", "rss_hive"),
        sqlalchemy_uri=os.getenv(
            "SUPERSET_DATABASE_URI",
            f"hive://{hive_host}:{hive_port}/{hive_database}",
        ),
        dataset_schema=os.getenv("SUPERSET_DATASET_SCHEMA", hive_database),
        dataset_table=os.getenv("SUPERSET_DATASET_TABLE", hive_table),
        dataset_label=os.getenv("SUPERSET_DATASET_LABEL", "RSS Articles"),
    )


def load_superset_app() -> Any:
    from superset.app import create_app

    superset_config_module = os.getenv("SUPERSET_CONFIG")
    return create_app(superset_config_module=superset_config_module)


def load_superset_models() -> tuple[Any, Any]:
    from superset.models.core import Database
    from superset.connectors.sqla.models import SqlaTable

    return Database, SqlaTable


def ensure_database(db_session: Any, database_model: Any, config: BootstrapConfig) -> Any:
    database = (
        db_session.query(database_model)
        .filter(database_model.database_name == config.database_name)
        .one_or_none()
    )

    if database is None:
        database = database_model(database_name=config.database_name)
        db_session.add(database)

    if hasattr(database, "set_sqlalchemy_uri"):
        database.set_sqlalchemy_uri(config.sqlalchemy_uri)
    else:
        database.sqlalchemy_uri = config.sqlalchemy_uri

    if hasattr(database, "expose_in_sqllab"):
        database.expose_in_sqllab = True

    if hasattr(database, "allow_ctas"):
        database.allow_ctas = True

    db_session.commit()
    logger.info("Superset database ready: %s", config.database_name)
    return database


def ensure_dataset(db_session: Any, dataset_model: Any, database: Any, config: BootstrapConfig) -> Any:
    query = db_session.query(dataset_model)

    filters = []
    if hasattr(dataset_model, "database_id"):
        filters.append(dataset_model.database_id == database.id)
    if hasattr(dataset_model, "schema"):
        filters.append(dataset_model.schema == config.dataset_schema)
    if hasattr(dataset_model, "table_name"):
        filters.append(dataset_model.table_name == config.dataset_table)

    for clause in filters:
        query = query.filter(clause)

    dataset = query.one_or_none()
    if dataset is None:
        dataset = dataset_model()
    if hasattr(dataset, "table_name"):
        dataset.table_name = config.dataset_table
    if hasattr(dataset, "schema"):
        dataset.schema = config.dataset_schema
    if hasattr(dataset, "verbose_name"):
        dataset.verbose_name = config.dataset_label
    if hasattr(dataset, "database"):
        dataset.database = database

    db_session.add(dataset)

    db_session.commit()
    return dataset


def refresh_dataset_metadata(dataset: Any, attempts: int = 10, delay_seconds: int = 5) -> None:
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            if hasattr(dataset, "fetch_metadata"):
                dataset.fetch_metadata()
            logger.info("Superset dataset metadata refreshed")
            return
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Failed to refresh Superset dataset metadata (%s/%s): %s",
                attempt,
                attempts,
                exc,
            )
            if attempt < attempts:
                time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error


def bootstrap() -> None:
    config = build_config()
    superset_app = load_superset_app()
    database_model, dataset_model = load_superset_models()

    with superset_app.app_context():
        from superset.extensions import db

        database = ensure_database(db.session, database_model, config)
        dataset = ensure_dataset(db.session, dataset_model, database, config)
        refresh_dataset_metadata(dataset)
        logger.info(
            "Superset bootstrap complete for %s / %s.%s",
            config.database_name,
            config.dataset_schema,
            config.dataset_table,
        )


if __name__ == "__main__":
    bootstrap()
