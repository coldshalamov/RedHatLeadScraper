"""Data models used throughout the lead verifier package."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(slots=True)
class LeadInput:
    """Normalized lead data passed to scrapers."""

    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LeadVerificationResult:
    """Container for scraper results."""

    lead: LeadInput
    source: str
    status: str
    details: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def as_row(self) -> Dict[str, Any]:
        """Return a serialisable representation of the result."""

        row = {
            "lead_name": self.lead.name,
            "lead_phone": self.lead.phone or "",
            "lead_email": self.lead.email or "",
            "source": self.source,
            "status": self.status,
            "details": self.details,
        }
        row.update({f"extra_{key}": value for key, value in self.extra.items()})
        return row
