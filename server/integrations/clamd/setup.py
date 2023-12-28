import contextlib
import logging
import socket
import time
from pathlib import Path

from .common import ClamdConfig, ClamdError, clamd_socket

_logger = logging.getLogger(__name__)


def initialise_container(config: ClamdConfig, *, timeout_s: int) -> None:
    """
    Initialise the clamav container, if it does not already exist.

    The equivalent in bash is:

    .. code-block:: bash

        export CLAMAV_IMAGE='clamav/clamav:latest_base'
        docker pull "${CLAMAV_IMAGE}"

        docker run \
          --name clamav \
          --detach \
          --rm \
          --publish 3310:3310 \
          --mount type=bind,source="$(pwd)/mounted",target=/var/lib/clamav \
          "${CLAMAV_IMAGE}"

    """
    image_tag = "clamav/clamav:latest_base"
    container_name = "clamav"

    try:
        import docker
        from docker.types import Mount
    except ModuleNotFoundError:
        _logger.warning("Docker module not found, skipping container initialisation")
        return

    client = docker.from_env()
    if client.containers.list(filters={"name": container_name}):
        _logger.info(
            "Container `%s` already exists, skipping container initialisation",
            container_name,
        )
        return

    mount_dir = Path(__file__).parent / "mounted"
    if not mount_dir.exists():
        mount_dir.mkdir()
        _logger.info("Created mount directory `%s`", mount_dir)

    client.containers.run(
        image_tag,
        name=container_name,
        detach=True,
        ports={f"{config.port}/tcp": config.port},
        mounts=(Mount("/var/lib/clamav", str(mount_dir.resolve()), type="bind"),),
    )
    _logger.info("Initialised container `%s`", container_name)

    # wait for container to start
    poll_interval = 5
    for _ in range(0, timeout_s + poll_interval - 1, poll_interval):
        with contextlib.suppress(ClamdError):
            if test_connection(config):
                return

        time.sleep(poll_interval)

    raise TimeoutError(f"Container failed to start within {timeout_s} seconds")


def test_connection(config: ClamdConfig) -> bool:
    with clamd_socket(config) as sock:
        try:
            _logger.debug("Sending PING...")
            sock.send(b"zPING\0")
            response = sock.recv(1024)
        except (OSError, socket.timeout):
            _logger.exception("Failed to connect to clamd")
            return False

        if response == b"PONG\0":
            _logger.debug("Received PONG")
            return True

        _logger.debug("Expected PONG, received: `%s`", response)
        return False
