import pandas as pd
import pytest

from lead_verifier.ingestion.loaders import UnsupportedFileTypeError, load_leads


@pytest.fixture()
def sample_dataframe():
    return pd.DataFrame(
        [
            {
                "Lead ID": "1",
                "Name": "Ada Lovelace",
                "Email 1": "ada@example.com",
                "Email 2": "ada+alt@example.com",
                "Phone Primary": "555-1111",
                "Phone Secondary": "555-2222",
                "Company": "Analytical Engines",
            },
            {
                "Lead ID": "2",
                "Name": "Grace Hopper",
                "Email 1": "",
                "Email 2": "grace@example.com",
                "Phone Primary": "555-3333",
                "Phone Secondary": "",
                "Company": "US Navy",
            },
        ]
    )


def test_load_leads_from_csv_with_mapping(sample_dataframe, tmp_path):
    csv_path = tmp_path / "leads.csv"
    sample_dataframe.to_csv(csv_path, index=False)

    leads = load_leads(
        csv_path,
        column_mapping={
            "source_id": "Lead ID",
            "full_name": "Name",
            "emails": ["Email 1", "Email 2"],
            "phones": ["Phone Primary", "Phone Secondary"],
            "company": "Company",
        },
    )

    assert len(leads) == 2
    first, second = leads
    assert first.source_id == "1"
    assert first.full_name == "Ada Lovelace"
    assert first.emails == ["ada@example.com", "ada+alt@example.com"]
    assert first.phones == ["555-1111", "555-2222"]
    assert second.emails == ["grace@example.com"]
    assert second.phones == ["555-3333"]


def test_load_leads_from_excel_with_automatic_mapping(sample_dataframe, tmp_path):
    excel_path = tmp_path / "leads.xlsx"
    sample_dataframe.rename(
        columns={
            "Lead ID": "record_id",
            "Name": "full_name",
            "Email 1": "email",
            "Email 2": "email_secondary",
            "Phone Primary": "phone",
            "Phone Secondary": "phone_alt",
        }
    ).to_excel(excel_path, index=False)

    leads = load_leads(excel_path)

    assert len(leads) == 2
    assert leads[0].source_id == "1"
    assert leads[0].full_name == "Ada Lovelace"
    assert leads[0].emails == ["ada@example.com", "ada+alt@example.com"]
    assert leads[0].phones == ["555-1111", "555-2222"]


def test_unsupported_file_extension(tmp_path):
    bad_path = tmp_path / "leads.json"
    bad_path.write_text("{}", encoding="utf-8")

    with pytest.raises(UnsupportedFileTypeError):
        load_leads(bad_path)
