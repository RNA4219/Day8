from pathlib import Path


def test_install_md_mentions_governance_policy():
    install_md = Path(__file__).resolve().parents[2] / "INSTALL.md"
    content = install_md.read_text(encoding="utf-8")

    assert "workflow-cookbook/governance/policy.yaml" in content
