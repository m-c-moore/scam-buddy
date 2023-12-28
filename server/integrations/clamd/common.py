import contextlib
import logging
import socket
from collections.abc import Generator

import pydantic

_logger = logging.getLogger(__name__)


class ClamdError(Exception):
    ...


class ClamdConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
    )

    host: str = pydantic.Field(pattern=r"^\w+$")
    port: int = pydantic.Field(ge=0, le=65535)
    timeout: float = pydantic.Field(ge=0)


@contextlib.contextmanager
def clamd_socket(config: ClamdConfig) -> Generator[socket.socket, None, None]:
    _logger.debug("Connecting to clamd at `%s:%d`...", config.host, config.port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((config.host, config.port))
            sock.settimeout(config.timeout)
            _logger.debug("Connected to clamd")
        except OSError as e:
            raise ClamdError(
                f"Failed connect to clamd at {config.host}:{config.port}",
            ) from e
        yield sock
