from pathlib import Path

from server.common import init_logging
from server.integrations.clamd.common import ClamdConfig
from server.integrations.clamd.query import scan_object
from server.integrations.clamd.setup import initialise_container

if __name__ == "__main__":
    init_logging(debug=True)
    _config = ClamdConfig(host="localhost", port=3310, timeout=10)
    initialise_container(_config, timeout_s=60)

    with Path("data/emails/forward_paypal.eml").open("rb") as f:
        _result = scan_object(f, _config)
