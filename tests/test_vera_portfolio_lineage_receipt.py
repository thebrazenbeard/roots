import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "portfolio" / "VERA_PORTFOLIO_LINEAGE_RECEIPT_V1.json"


def test_vera_portfolio_lineage_receipt_preserves_conflict_and_non_lineage() -> None:
    data = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert data["schema"] == "ROOTS_VERA_PORTFOLIO_LINEAGE_RECEIPT_V1"

    findings = {item["subject"]: item for item in data["findings"]}

    assert findings["VERA_RELEASE"]["conclusion"] == "ESTABLISHED_SUPERSESSION_OF_CONTROL_LINE"
    assert findings["BUILD_TEAM_2_VS_BT2"]["conclusion"] == "NO_SUPERSESSION_RELATION_ESTABLISHED"

    hc = findings["HC_TEMPLATE_CANONICALITY"]
    assert hc["confidence"] == "UNRESOLVED"
    assert hc["conclusion"] == "UNRESOLVED_MULTIPLE_CURRENT_CANONICALITY_CLAIMS"
    assert set(hc["claimants"]) == {
        "thebrazenbeard/self",
        "thebrazenbeard/hc-brain",
        "thebrazenbeard/bt2",
    }

    wb = findings["WORKBRIDGE_VERAMESH_BYTE_OVERLAP"]
    assert wb["relation"] == "REUSE"
    assert "NO_ORIGIN_OR_SUCCESSION_ESTABLISHED" in wb["conclusion"]

    redworm = findings["REDWORM_PROVIDER_AUTHORSHIP"]
    assert redworm["confidence"] == "UNRESOLVED"
    assert redworm["conclusion"] == "HISTORICAL_SOURCE_AUTHORSHIP_UNRESOLVED"

    assert data["conflicts"]
    assert any(item["gap_id"] == "FULL_E2E_QUALIFICATION" for item in data["gaps"])
