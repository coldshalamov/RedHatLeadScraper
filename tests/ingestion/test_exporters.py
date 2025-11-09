import pandas as pd

from lead_verifier.ingestion.exporters import export_lead_results, results_to_dataframe
from lead_verifier.ingestion.models import EmailRecord, LeadInput, LeadResult, PhoneRecord


def _build_sample_result() -> LeadResult:
    lead = LeadInput(
        source_id="1",
        full_name="Ada Lovelace",
        first_name="Ada",
        last_name="Lovelace",
        company="Analytical Engines",
        emails=["ada@example.com", "ada+alt@example.com"],
        phones=["555-1111", "555-2222"],
        metadata={"region": "UK"},
    )
    return LeadResult(
        lead=lead,
        email_records=[
            EmailRecord(address="ada@example.com", status="valid"),
            EmailRecord(address="ada+alt@example.com", status="valid", reason="secondary"),
        ],
        phone_records=[
            PhoneRecord(number="555-1111", status="connected", carrier="BT"),
            PhoneRecord(number="555-2222", status="connected", line_type="mobile"),
        ],
        notes="Confirmed",
    )


def test_results_to_dataframe_includes_metadata_and_records():
    dataframe = results_to_dataframe([_build_sample_result()], include_metadata=True, include_raw_records=True)

    required_columns = {
        "source_id",
        "full_name",
        "emails",
        "phones",
        "email_records",
        "phone_records",
        "notes",
        "metadata.region",
        "email_records_raw",
        "phone_records_raw",
    }
    assert required_columns.issubset(dataframe.columns)
    row = dataframe.iloc[0]
    assert "ada@example.com" in row["emails"]
    assert "555-1111" in row["phones"]
    assert isinstance(row["email_records_raw"], list)
    assert isinstance(row["phone_records_raw"], list)


def test_export_lead_results_to_csv_and_excel(tmp_path):
    results = [_build_sample_result()]

    csv_path = tmp_path / "results.csv"
    excel_path = tmp_path / "results.xlsx"

    export_lead_results(results, csv_path)
    export_lead_results(results, excel_path)

    csv_frame = pd.read_csv(csv_path)
    excel_frame = pd.read_excel(excel_path)

    assert csv_frame.loc[0, "full_name"] == "Ada Lovelace"
    assert "ada@example.com" in csv_frame.loc[0, "emails"]
    assert excel_frame.loc[0, "phone_records"].startswith("555-1111")
