import logging
from pathlib import Path
from typing import Final

CACHE_DIR: Final = Path("data/cache")


def init_logging(*, debug: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s.%(msecs)03d | %(levelname)-7s | [%(module)s] %(message)s",
        handlers=[logging.StreamHandler()],
        datefmt="%H:%M:%S",
    )
