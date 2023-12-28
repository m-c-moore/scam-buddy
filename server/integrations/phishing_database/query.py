import logging
import sqlite3
from pathlib import Path

from server.common import init_logging

_logger = logging.getLogger(__name__)


def is_domain_phishing(domain: str) -> bool:
    database_path = Path(__file__).parent / "database.sqlite"

    with sqlite3.connect(database_path) as conn:
        cursor = conn.execute("SELECT 1 FROM domains WHERE domain = ?", (domain,))
        return cursor.fetchone() is not None


if __name__ == "__main__":
    init_logging()
    is_domain_phishing("google.com")
    is_domain_phishing("accounts-gmall.cf")
