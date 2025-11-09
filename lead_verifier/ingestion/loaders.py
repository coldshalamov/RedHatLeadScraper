"""Utilities for loading lead data from spreadsheets."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Union

import pandas as pd

from .models import LeadInput

PathLike = Union[str, Path]

_FIELD_SYNONYMS: Mapping[str, Sequence[str]] = {
    "source_id": ("source_id", "id", "lead_id", "record_id"),
    "full_name": ("full_name", "name"),
    "first_name": ("first_name", "firstname", "first"),
    "last_name": ("last_name", "lastname", "last"),
    "company": ("company", "organisation", "organization", "employer"),
    "emails": ("emails", "email", "email_address", "primary_email"),
    "phones": ("phones", "phone", "phone_number", "primary_phone"),
}


class UnsupportedFileTypeError(ValueError):
    """Raised when an unsupported file format is passed to the loader."""


def load_leads(
    path: PathLike,
    *,
    column_mapping: Optional[Mapping[str, Union[str, Sequence[str]]]] = None,
    sheet_name: Union[str, int, None] = 0,
    loader_kwargs: Optional[MutableMapping[str, Any]] = None,
) -> List[LeadInput]:
    """Load lead records from a spreadsheet.

    Parameters
    ----------
    path:
        Path to the CSV/XLSX file to be loaded.
    column_mapping:
        Optional mapping of :class:`LeadInput` field names to column names (or
        sequences of column names for list fields such as ``emails``).
    sheet_name:
        Sheet selector passed to :func:`pandas.read_excel` when loading an Excel
        file. Ignored for CSV files.
    loader_kwargs:
        Extra keyword arguments forwarded to :func:`pandas.read_csv` or
        :func:`pandas.read_excel`.
    """

    dataframe = _read_dataframe(path, sheet_name=sheet_name, loader_kwargs=loader_kwargs)
    mapping = dict(column_mapping or {})
    leads: List[LeadInput] = []

    for _, row in dataframe.iterrows():
        if _row_is_empty(row):
            continue
        leads.append(_row_to_lead(row, dataframe.columns, mapping))

    return leads


def _read_dataframe(
    path: PathLike,
    *,
    sheet_name: Union[str, int, None] = 0,
    loader_kwargs: Optional[MutableMapping[str, Any]] = None,
) -> pd.DataFrame:
    loader_kwargs = dict(loader_kwargs or {})
    path_obj = Path(path)
    suffix = path_obj.suffix.lower()

    if suffix in {".csv", ".tsv"}:
        if suffix == ".tsv":
            loader_kwargs.setdefault("sep", "\t")
        return pd.read_csv(path_obj, **loader_kwargs)

    if suffix in {".xls", ".xlsx", ".xlsm", ".xlsb"}:
        return pd.read_excel(path_obj, sheet_name=sheet_name, engine=loader_kwargs.pop("engine", None) or "openpyxl", **loader_kwargs)

    raise UnsupportedFileTypeError(f"Unsupported file extension: {path_obj.suffix}")


def _row_is_empty(row: pd.Series) -> bool:
    return all(pd.isna(value) or (isinstance(value, str) and not value.strip()) for value in row.values)


def _row_to_lead(
    row: pd.Series,
    columns: Iterable[str],
    mapping: Mapping[str, Union[str, Sequence[str]]],
) -> LeadInput:
    resolved_columns = {field: _resolve_columns(field, columns, mapping) for field in _FIELD_SYNONYMS}

    source_id = _extract_scalar(row, resolved_columns["source_id"])
    full_name = _extract_scalar(row, resolved_columns["full_name"])
    first_name = _extract_scalar(row, resolved_columns["first_name"])
    last_name = _extract_scalar(row, resolved_columns["last_name"])
    company = _extract_scalar(row, resolved_columns["company"])
    emails = _extract_list(row, resolved_columns["emails"])
    phones = _extract_list(row, resolved_columns["phones"])

    metadata = {
        column: value
        for column, value in row.items()
        if not pd.isna(value) and (not isinstance(value, str) or value.strip())
    }

    if source_id:
        metadata["source_id"] = source_id
    if company:
        metadata["company"] = company
    if full_name:
        metadata["full_name"] = full_name
    metadata["emails"] = emails
    metadata["phones"] = phones
    if first_name:
        metadata["first_name"] = first_name
    if last_name:
        metadata["last_name"] = last_name

    name = full_name or " ".join(filter(None, [first_name, last_name])) or None
    primary_email = emails[0] if emails else None
    primary_phone = phones[0] if phones else None

    return LeadInput(
        name=name,
        phone=primary_phone,
        email=primary_email,
        first_name=first_name,
        last_name=last_name,
        metadata=metadata,
    )


def _resolve_columns(
    field: str,
    available_columns: Iterable[str],
    mapping: Mapping[str, Union[str, Sequence[str]]],
) -> List[str]:
    if field in mapping:
        return _normalize_column_spec(mapping[field])

    synonyms = tuple(name.lower() for name in _FIELD_SYNONYMS.get(field, (field,)))
    resolved: List[str] = []

    for column in available_columns:
        column_lc = column.lower()
        for synonym in synonyms:
            if column_lc == synonym or column_lc.startswith(f"{synonym}_") or column_lc.startswith(f"{synonym} "):
                resolved.append(column)
                break

    return resolved


def _normalize_column_spec(value: Union[str, Sequence[str]]) -> List[str]:
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _extract_scalar(row: pd.Series, columns: Sequence[str]) -> Optional[str]:
    for column in columns:
        if column not in row:
            continue
        value = row[column]
        text = _clean_text(value)
        if text is not None:
            return text
    return None


def _extract_list(row: pd.Series, columns: Sequence[str]) -> List[str]:
    results: List[str] = []
    for column in columns:
        if column not in row:
            continue
        text = _clean_text(row[column])
        if text and text not in results:
            results.append(text)
    return results


def _clean_text(value: Any) -> Optional[str]:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    text = str(value).strip()
    return text or None


__all__ = ["load_leads", "UnsupportedFileTypeError"]
