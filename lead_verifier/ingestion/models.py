"""Data models used by lead ingestion utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class LeadInput:
    """Normalized representation of a lead imported from a spreadsheet."""

    source_id: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PhoneRecord:
    """Verification information about a phone number."""

    number: str
    status: Optional[str] = None
    line_type: Optional[str] = None
    carrier: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EmailRecord:
    """Verification information about an email address."""

    address: str
    status: Optional[str] = None
    reason: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LeadResult:
    """Aggregated verification results for a lead."""

    lead: LeadInput
    phone_records: List[PhoneRecord] = field(default_factory=list)
    email_records: List[EmailRecord] = field(default_factory=list)
    notes: Optional[str] = None


__all__ = [
    "LeadInput",
    "LeadResult",
    "PhoneRecord",
    "EmailRecord",
]
