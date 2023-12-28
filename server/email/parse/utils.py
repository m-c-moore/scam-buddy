import pydantic
from urlextract import URLExtract

from server.common import CACHE_DIR

_URL_EXTRACTOR_IGNORE_LIST = frozenset(
    (
        "www.w3.org",
        "fonts.googleapis.com",
    ),
)


def extract_urls_from_html(
    text: str,
    *,
    limit: int = 1_000,
) -> tuple[pydantic.AnyUrl, ...]:
    cache_dir = CACHE_DIR / "urlextract"
    cache_dir.mkdir(parents=True, exist_ok=True)

    extractor = URLExtract(
        extract_email=False,
        cache_dns=True,  # TODO: does this get used?
        extract_localhost=True,
        limit=limit,
        allow_mixed_case_hostname=True,
        cache_dir=cache_dir,
    )
    extractor.ignore_list = _URL_EXTRACTOR_IGNORE_LIST
    return tuple(map(pydantic.AnyUrl, extractor.find_urls(text)))
