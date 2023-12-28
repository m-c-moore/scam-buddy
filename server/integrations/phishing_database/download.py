import logging
import sqlite3
import tarfile
import tempfile
from pathlib import Path

import requests
from tqdm import tqdm

from server.common import init_logging

_logger = logging.getLogger(__name__)


def main() -> None:
    download_url = (
        "https://raw.githubusercontent.com/mitchellkrogza"
        "/Phishing.Database/master/ALL-phishing-domains.tar.gz"
    )
    database_path = Path(__file__).parent / "database.sqlite"
    commit_every = 10_000

    with tempfile.TemporaryDirectory() as temp_dir:
        _logger.info("Downloading...")
        response = requests.get(download_url, timeout=10)
        response.raise_for_status()

        _logger.info("Writing...")
        tar_file_path = Path(temp_dir) / "out.tar.gz"
        tar_file_path.write_bytes(response.content)

        _logger.info("Extracting...")
        with tarfile.open(tar_file_path) as tar_file:
            tar_file.extractall(temp_dir)

        text_file_path = Path(temp_dir) / "ALL-phishing-domains.txt"

        _logger.info("Creating database...")
        with sqlite3.connect(database_path) as conn:
            conn.execute("DROP TABLE IF EXISTS domains")
            conn.execute("CREATE TABLE domains (domain TEXT PRIMARY KEY)")

            with text_file_path.open() as text_file:
                for i, line in enumerate(
                    tqdm(
                        text_file,
                        desc="Inserting",
                        unit=" line",
                        total=630_000,  # approximate
                    ),
                ):
                    conn.execute(
                        "INSERT INTO domains (domain) VALUES (?)",
                        (line.strip(),),
                    )
                    if i % commit_every == 0:
                        conn.commit()

            conn.commit()


if __name__ == "__main__":
    init_logging()
    main()
