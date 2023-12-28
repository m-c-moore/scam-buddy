from __future__ import annotations

from datetime import datetime
from functools import cached_property
from ipaddress import IPv4Address, IPv6Address, ip_address
from pathlib import Path
from typing import Self

import mailparser
import pydantic

from server.email.parse.utils import extract_urls_from_html

_model_config = pydantic.ConfigDict(
    extra="forbid",
    strict=True,
    frozen=True,
)


class EmailPerson(pydantic.BaseModel):
    model_config = _model_config

    name: str | None = pydantic.Field(pattern=r"^[\w\s]+$")
    address: pydantic.EmailStr

    @classmethod
    def from_tuple(cls, tup: tuple[str, str]) -> Self:
        name, address = tup
        name = name.strip()
        address = address.strip()
        return cls(name=name or None, address=address)

    @cached_property
    def domain(self) -> str:
        return self.address.split("@", 1)[1]


class EmailBody(pydantic.BaseModel):
    model_config = _model_config

    text: str
    html: str

    @classmethod
    def from_message(cls, m: mailparser.MailParser) -> Self:
        text = "\n".join(m.text_plain)
        html = "\n".join(m.text_html)
        return cls(text=text, html=html)

    @cached_property
    def urls(self) -> tuple[pydantic.AnyUrl, ...]:
        return extract_urls_from_html(self.html)


class EmailMessage(pydantic.BaseModel):
    model_config = _model_config

    sender: EmailPerson
    receiver: EmailPerson
    date: datetime
    subject: str
    body: EmailBody
    ip_address: IPv4Address | IPv6Address

    @classmethod
    def from_file(cls, path: Path) -> Self:
        m = mailparser.parse_from_file(str(path.resolve()))

        return cls(
            sender=EmailPerson.from_tuple(m.from_[0]),
            receiver=EmailPerson.from_tuple(m.to[0]),
            date=m.date,
            subject=m.subject,
            body=EmailBody.from_message(m),
            ip_address=ip_address("1.2.3.4"),  # TODO
        )


if __name__ == "__main__":
    email_dir_path = Path("data/emails")
    message = EmailMessage.from_file(email_dir_path / "hybrid_analysis.eml")
