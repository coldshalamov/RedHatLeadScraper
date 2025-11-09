"""Export utilities for verified lead data."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, MutableMapping, Optional, Sequence, Union

import pandas as pd

from .models import EmailRecord, LeadResult, PhoneRecord

PathLike = Union[str, Path]


def export_lead_results(
    results: Sequence[LeadResult],
    path: PathLike,
    *,
    include_metadata: bool = True,
    include_raw_records: bool = False,
    sheet_name: str = "Results",
    exporter_kwargs: Optional[MutableMapping[str, object]] = None,
) -> Path:
    """Write lead verification results to a CSV or Excel file."""

    dataframe = results_to_dataframe(
        results,
        include_metadata=include_metadata,
        include_raw_records=include_raw_records,
    )
    output_path = Path(path)
    _write_dataframe(dataframe, output_path, sheet_name=sheet_name, exporter_kwargs=exporter_kwargs)
    return output_path


def results_to_dataframe(
    results: Sequence[LeadResult],
    *,
    include_metadata: bool = True,
    include_raw_records: bool = False,
) -> pd.DataFrame:
    """Convert verification results into a :class:`pandas.DataFrame`."""

    records = [
        _result_to_row(result, include_metadata=include_metadata, include_raw_records=include_raw_records)
        for result in results
    ]
    return pd.DataFrame(records)


def _result_to_row(
    result: LeadResult,
    *,
    include_metadata: bool,
    include_raw_records: bool,
) -> MutableMapping[str, object]:
    row: MutableMapping[str, object] = {
        "source_id": result.lead.source_id,
        "full_name": result.lead.full_name,
        "first_name": result.lead.first_name,
        "last_name": result.lead.last_name,
        "company": result.lead.company,
        "emails": _join_list(result.lead.emails),
        "phones": _join_list(result.lead.phones),
        "email_records": _join_list(_format_email_record(record) for record in result.email_records),
        "phone_records": _join_list(_format_phone_record(record) for record in result.phone_records),
        "notes": result.notes,
    }

    if include_metadata:
        for key, value in result.lead.metadata.items():
            row[f"metadata.{key}"] = value

    if include_raw_records:
        row["email_records_raw"] = [asdict(record) for record in result.email_records]
        row["phone_records_raw"] = [asdict(record) for record in result.phone_records]

    return row


def _join_list(values: Iterable[Optional[str]]) -> str:
    cleaned: List[str] = []
    for value in values:
        if not value:
            continue
        text = str(value).strip()
        if text:
            cleaned.append(text)
    return "; ".join(cleaned)


def _format_phone_record(record: PhoneRecord) -> str:
    parts: List[str] = [record.number]
    annotations: List[str] = []
    if record.status:
        annotations.append(record.status)
    if record.line_type:
        annotations.append(record.line_type)
    if record.carrier:
        annotations.append(record.carrier)
    if annotations:
        parts.append(f"({', '.join(annotations)})")
    return " ".join(parts)


def _format_email_record(record: EmailRecord) -> str:
    parts: List[str] = [record.address]
    annotations: List[str] = []
    if record.status:
        annotations.append(record.status)
    if record.reason:
        annotations.append(record.reason)
    if annotations:
        parts.append(f"({', '.join(annotations)})")
    return " ".join(parts)


def _write_dataframe(
    dataframe: pd.DataFrame,
    path: Path,
    *,
    sheet_name: str,
    exporter_kwargs: Optional[MutableMapping[str, object]],
) -> None:
    exporter_kwargs = dict(exporter_kwargs or {})
    suffix = path.suffix.lower()

    if suffix in {".csv", ".tsv"}:
        if suffix == ".tsv":
            exporter_kwargs.setdefault("sep", "\t")
        dataframe.to_csv(path, index=False, **exporter_kwargs)
        return

    if suffix in {".xls", ".xlsx", ".xlsm", ".xlsb"}:
        engine = exporter_kwargs.pop("engine", None) or "openpyxl"
        dataframe.to_excel(path, index=False, sheet_name=sheet_name, engine=engine, **exporter_kwargs)
        return

    raise ValueError(f"Unsupported export file extension: {suffix}")


__all__ = ["export_lead_results", "results_to_dataframe"]
