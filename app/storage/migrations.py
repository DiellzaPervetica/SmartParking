from __future__ import annotations

from pathlib import Path

from app.logging_config import configure_logging
from app.storage.cassandra_client import CassandraConnection

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "config" / "cassandra" / "init.cql"


def main() -> None:
    configure_logging()
    connection = CassandraConnection()
    connection.execute_script(SCHEMA_FILE)
    print("Cassandra schema initialized successfully.")


if __name__ == "__main__":
    main()
