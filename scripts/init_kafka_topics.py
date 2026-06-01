from __future__ import annotations

from app.logging_config import configure_logging
from app.streaming.topic_manager import create_default_topics


def main() -> None:
    configure_logging()
    create_default_topics()
    print("Kafka topics initialized.")


if __name__ == "__main__":
    main()
