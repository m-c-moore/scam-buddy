import contextlib
import enum
import logging
import re
import socket
import struct
from typing import BinaryIO, Self

import pydantic

from .common import ClamdConfig, ClamdError, clamd_socket

_logger = logging.getLogger(__name__)

_SCAN_RESPONSE_PATTERN = re.compile(
    r"^stream: ((?P<message>.+) )?(?P<status>(FOUND|OK|ERROR))\0?$",
)
_CHUNK_SIZE = 1024  # <= StreamMaxLength


class ClamdScanStatus(enum.StrEnum):
    OK = "OK"  # no virus found
    FOUND = "FOUND"  # found a virus
    ERROR = "ERROR"  # error during scan


class ClamdScanResult(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
    )

    status: ClamdScanStatus
    message: str | None

    @classmethod
    def from_response(cls, response: str) -> Self:
        match = _SCAN_RESPONSE_PATTERN.match(response)
        if match is None:
            raise ValueError(f"Invalid response: `{response}`")

        return cls(
            status=ClamdScanStatus(match.group("status")),
            message=match.group("message"),
        )

    @pydantic.field_validator("message")
    @classmethod
    def validate_message(
        cls,
        message: str | None,
        info: pydantic.ValidationInfo,
    ) -> str | None:
        status: ClamdScanStatus = info.data["status"]

        if message is None:
            if status is not ClamdScanStatus.OK:
                raise ValueError("Message must be provided when status is not OK")
            return message

        if status is ClamdScanStatus.OK:
            raise ValueError("Message must be None when status is OK")

        return message.strip()


def scan_object(obj: BinaryIO, config: ClamdConfig) -> ClamdScanResult:
    sock: socket.socket
    with clamd_socket(config) as sock:
        try:
            _logger.debug("Scanning object...")
            sock.send(b"zINSTREAM\0")
            while chunk := obj.read(_CHUNK_SIZE):
                size = struct.pack(b"!L", len(chunk))
                sock.send(size + chunk)
            sock.send(struct.pack(b"!L", 0))
        except (OSError, socket.timeout) as e:
            raise ClamdError("Failed to scan object") from e

        with contextlib.closing(sock.makefile("rb")) as f:
            response = f.readline().decode("utf-8")

    result = ClamdScanResult.from_response(response)
    _logger.debug("Scan complete, status '%s'", result.status)
    return result
