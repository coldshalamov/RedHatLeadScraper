"""Shared data structures for lead verification scrapers.

The :mod:`lead_verifier.scrapers` modules exchange structured data via these
simple dataclasses.  They intentionally avoid any heavy dependencies so they
can be reused by CLIs, web services or notebooks without additional setup.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PersonSearch:
    """Input parameters used by scrapers to look up a person.

    Attributes
    ----------
    first_name:
        The person's given name.  Optional, but at least one of
        ``first_name`` and ``last_name`` must be provided.
    last_name:
        The person's family name.
    city_state_zip:
        Optional location hint such as ``"Austin, TX"`` or a zip code.  The
        scrapers simply append this string to the provider specific search
        field.
    """

    first_name: str = ""
    last_name: str = ""
    city_state_zip: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Return the combined name string suitable for query parameters."""

        return " ".join(part for part in (self.first_name.strip(), self.last_name.strip()) if part).strip()

    def require_name(self) -> None:
        """Ensure that at least one name component is present.

        Raises
        ------
        ValueError
            If neither a first nor last name was provided.
        """

        if not self.full_name:
            raise ValueError("At least one of first_name or last_name must be provided.")


@dataclass
class EmailRecord:
    """Represents a single email address discovered for a lead."""

    address: str
    label: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScraperNotes:
    """Diagnostic information collected during a scraping session."""

    messages: List[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        self.messages.append(message)


@dataclass
class ScraperResult:
    """Normalized response returned by scrapers."""

    provider: str
    query: PersonSearch
    found: bool
    emails: List[EmailRecord] = field(default_factory=list)
    notes: ScraperNotes = field(default_factory=ScraperNotes)

    def add_email(self, address: str, label: Optional[str] = None, **metadata: str) -> None:
        self.emails.append(EmailRecord(address=address, label=label, metadata=metadata))

    def add_note(self, message: str) -> None:
        self.notes.add(message)
