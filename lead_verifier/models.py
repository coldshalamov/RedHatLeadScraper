"""Shared data models and structures for lead verification scrapers and workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# --- Input Models ---

@dataclass
class PersonSearch:
    """Input parameters used by scrapers to look up a person.

    Attributes
    ----------
    first_name:
        The person's given name. Optional, but at least one of
        ``first_name`` and ``last_name`` must be provided.
    last_name:
        The person's family name.
    city_state_zip:
        Optional location hint such as ``"Austin, TX"`` or a zip code. The
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
        """Ensure that at least one name component is present."""
        if not self.full_name:
            raise ValueError("At least one of first_name or last_name must be provided.")


@dataclass(slots=True)
class LeadInput:
    """Minimal information required to query a lead."""

    first_name: str
    last_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None


# --- Result Models ---

@dataclass
class EmailRecord:
    """Represents a single email address discovered for a lead."""

    address: str
    label: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class PhoneNumberResult:
    """Represents a phone number discovered for a lead."""

    phone_number: str
    label: Optional[str] = None
    is_primary: Optional[bool] = None
    raw_text: Optional[str] = None


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


@dataclass(slots=True)
class LeadResult:
    """Normalized result returned by individual scrapers."""

    lead: LeadInput
    phone_numbers: List[PhoneNumberResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
