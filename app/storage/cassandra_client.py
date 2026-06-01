from __future__ import annotations

from pathlib import Path

from app.settings import get_settings


class CassandraConnection:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.cluster = None
        self.session = None

    def connect(self, with_keyspace: bool = True):
        if self.session is not None:
            return self.session

        try:
            from cassandra.cluster import Cluster
            from cassandra.query import dict_factory
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Cassandra driver is not available in this Python runtime. "
                "Use the lightweight simulation endpoint or run the full stack "
                "with a Cassandra-compatible Python environment."
            ) from exc

        self.cluster = Cluster(
            list(self.settings.cassandra_hosts),
            port=self.settings.cassandra_port,
            protocol_version=4,
        )
        self.session = self.cluster.connect()
        self.session.row_factory = dict_factory

        if with_keyspace:
            self.session.set_keyspace(self.settings.cassandra_keyspace)
        return self.session

    def shutdown(self) -> None:
        if self.session is not None:
            self.session.shutdown()
            self.session = None
        if self.cluster is not None:
            self.cluster.shutdown()
            self.cluster = None

    def execute_script(self, script_path: Path) -> None:
        session = self.connect(with_keyspace=False)
        content = script_path.read_text(encoding="utf-8")
        for statement in [chunk.strip() for chunk in content.split(";") if chunk.strip()]:
            session.execute(statement)
