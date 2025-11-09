"""Shared data models for the lead verification workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class LeadInput:
    """Minimal information required to query a lead."""

    first_name: str
    last_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None


@dataclass(slots=True)
class PhoneNumberResult:
    """Represents a phone number discovered for a lead."""

    phone_number: str
    label: Optional[str] = None
    is_primary: Optional[bool] = None
    raw_text: Optional[str] = None


@dataclass(slots=True)
class LeadResult:
    """Normalized result returned by individual scrapers."""

    lead: LeadInput
    phone_numbers: List[PhoneNumberResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
