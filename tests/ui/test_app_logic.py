from __future__ import annotations

import threading

import pytest

from lead_verifier.io import write_results
from lead_verifier.orchestrator import VerificationOrchestrator
from lead_verifier.scrapers.sample import EchoScraper
from lead_verifier.ui.app import normalise_lead_row, run_verification_job


def test_normalise_lead_row_populates_core_fields() -> None:
    row = {
        "Name": "Jane Doe",
        "Phone": "555-0100",
        "Email": "jane@example.com",
        "City": "Denver",
    }
    mapping = {"name": "Name", "phone": "Phone", "email": "Email", "city": "City"}

    lead = normalise_lead_row(row, mapping)

    assert lead.name == "Jane Doe"
    assert lead.first_name == "Jane"
    assert lead.last_name == "Doe"
    assert lead.phone == "555-0100"
    assert lead.email == "jane@example.com"
    assert lead.city == "Denver"
    assert lead.metadata["city"] == "Denver"


def test_run_verification_job_emits_progress_and_results(tmp_path) -> None:
    rows = [
        {"Name": "Alice Example", "Phone": "555-1111", "Email": "alice@example.com", "City": "Boston"},
        {"Name": "Bob Example", "Phone": "555-2222", "Email": "bob@example.com", "City": "Austin"},
    ]
    mapping = {"name": "Name", "phone": "Phone", "email": "Email", "city": "City"}
    orchestrator = VerificationOrchestrator([EchoScraper()])

    progress_events: list[tuple[int, int]] = []
    result_events: list = []

    aggregated = run_verification_job(
        orchestrator,
        rows,
        mapping,
        progress_callback=lambda current, total: progress_events.append((current, total)),
        result_callback=lambda result: result_events.append(result),
    )

    assert aggregated == result_events
    assert progress_events == [(1, 2), (2, 2)]
    assert len(aggregated) == 2

    first = aggregated[0]
    assert first.lead.name == "Alice Example"
    assert first.lead.city == "Boston"
    assert any(contact.value == "555-1111" for contact in first.contacts)
    assert any("echo" in contact.sources for contact in first.contacts)

    csv_path = tmp_path / "results.csv"
    write_results(csv_path, aggregated)
    content = csv_path.read_text(encoding="utf-8")
    assert "contacts" in content
    assert "Alice Example" in content

    if pytest.importorskip("openpyxl", reason="Excel export requires openpyxl"):
        excel_path = tmp_path / "results.xlsx"
        write_results(excel_path, aggregated)
        assert excel_path.exists()


def test_run_verification_job_respects_cancellation() -> None:
    rows = [
        {"Name": "Carol Example", "Phone": "555-3333", "Email": "carol@example.com"},
        {"Name": "Dan Example", "Phone": "555-4444", "Email": "dan@example.com"},
    ]
    mapping = {"name": "Name", "phone": "Phone", "email": "Email"}
    orchestrator = VerificationOrchestrator([EchoScraper()])
    cancel_event = threading.Event()

    aggregated = run_verification_job(
        orchestrator,
        rows,
        mapping,
        cancel_event=cancel_event,
        result_callback=lambda _: cancel_event.set(),
    )

    assert len(aggregated) == 1
    assert cancel_event.is_set()
    assert aggregated[0].lead.name == "Carol Example"
