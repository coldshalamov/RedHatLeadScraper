"""Domain models used by the lead verification orchestrator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class LeadInput:
    """Input data used to query scrapers for contact verification."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ContactDetail:
    """Represents a phone number, email address, or other contact detail."""

    type: str
    value: str


@dataclass(frozen=True)
class LeadVerification:
    """Result produced by an individual scraper."""

    source: str
    contacts: Iterable[ContactDetail] = field(default_factory=list)
    raw_data: Optional[dict] = None


@dataclass(frozen=True)
class AggregatedContact:
    """A merged contact detail annotated with all contributing sources."""

    type: str
    value: str
    sources: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AggregatedLeadResult:
    """Combined result for a single lead after merging scraper outputs."""

    lead: LeadInput
    contacts: List[AggregatedContact] = field(default_factory=list)
    raw_results: List[LeadVerification] = field(default_factory=list)
