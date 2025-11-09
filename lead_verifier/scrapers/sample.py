"""Example scraper implementations that operate on local data."""
from __future__ import annotations

from typing import List

from ..models import ContactDetail, LeadInput, LeadVerification


class EchoScraper:
    """Simple scraper that echoes contact details already present on the lead input."""

    name = "echo"

    def __init__(self, include_metadata: bool = False) -> None:
        self._include_metadata = include_metadata

    def verify(self, lead: LeadInput) -> LeadVerification:
        contacts: List[ContactDetail] = []
        if lead.phone:
            contacts.append(ContactDetail(type="phone", value=str(lead.phone)))
        if lead.email:
            contacts.append(ContactDetail(type="email", value=str(lead.email)))
        raw_data = lead.metadata if self._include_metadata else None
        return LeadVerification(source=self.name, contacts=contacts, raw_data=raw_data)
