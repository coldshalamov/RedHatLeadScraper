"""Unified data models for the lead verification orchestrator, scrapers, and GUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


# --- Core Input Models ---

@dataclass(slots=True)
class LeadInput:
    """Normalized lead data passed to scrapers and orchestrators."""

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def display_name(self) -> str:
        """Return a readable name for UI or logs."""
        if self.name:
            return self.name
        return " ".join(filter(None, [self.first_name, self.last_name])).strip() or "(Unnamed Lead)"

    @property
    def full_name(self) -> Optional[str]:
        """Alias for :attr:`name` to support legacy callers."""

        return self.name

    @property
    def source_id(self) -> Optional[str]:
        return self.metadata.get("source_id")

    @property
    def company(self) -> Optional[str]:
        return self.metadata.get("company")

    @property
    def city(self) -> Optional[str]:
        return self.metadata.get("city")

    @property
    def state(self) -> Optional[str]:
        return self.metadata.get("state")

    @property
    def address(self) -> Optional[str]:
        return self.metadata.get("address")

    @property
    def phones(self) -> List[str]:
        phones = self.metadata.get("phones", [])
        if isinstance(phones, list):
            return phones
        if phones is None:
            return []
        return [str(phones)]

    @property
    def emails(self) -> List[str]:
        emails = self.metadata.get("emails", [])
        if isinstance(emails, list):
            return emails
        if emails is None:
            return []
        return [str(emails)]


# --- GUI / CLI Verification Result ---

@dataclass(slots=True)
class LeadVerificationResult:
    """Container for scraper results (used by the GUI/CLI exporter)."""

    lead: LeadInput
    source: str
    status: str
    details: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def as_row(self) -> Dict[str, Any]:
        """Return a serialisable representation of the result."""
        row = {
            "lead_name": self.lead.display_name(),
            "lead_phone": self.lead.phone or "",
            "lead_email": self.lead.email or "",
            "source": self.source,
            "status": self.status,
            "details": self.details,
        }
        row.update({f"extra_{key}": value for key, value in self.extra.items()})
        return row


# --- Orchestrator & Scraper-Level Models ---

@dataclass
class ContactDetail:
    """Represents a phone number, email address, or other contact detail."""

    type: str
    value: str


@dataclass
class LeadVerification:
    """Result produced by an individual scraper."""

    source: str
    contacts: Iterable[ContactDetail] = field(default_factory=list)
    raw_data: Optional[dict] = None


@dataclass
class AggregatedContact:
    """A merged contact detail annotated with all contributing sources."""

    type: str
    value: str
    sources: List[str] = field(default_factory=list)


@dataclass
class AggregatedLeadResult:
    """Combined result for a single lead after merging scraper outputs."""

    lead: LeadInput
    contacts: List[AggregatedContact] = field(default_factory=list)
    raw_results: List[LeadVerification] = field(default_factory=list)


# --- Scraper Results (for individual site responses) ---

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
    query: LeadInput
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
