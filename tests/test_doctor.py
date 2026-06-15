"""Tests for AOCS setup diagnostics."""

import os
from unittest.mock import patch

from aocs_mcp.doctor import checks_to_dict, format_checks, run_doctor


def test_doctor_warns_when_no_provider_key():
    clean_env = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
    clean_env.pop("OPENCODE_API_KEY", None)

    with patch.dict(os.environ, clean_env, clear=True):
        checks = run_doctor(include_opencode=False)

    result = checks_to_dict(checks)
    assert result["failures"] == 0
    assert any(check.name == "model API environment" and check.status == "warn" for check in checks)


def test_doctor_reports_provider_key_without_revealing_secret():
    with patch.dict(os.environ, {"OPENCODE_API_KEY": "dummy-api-key"}, clear=True):
        checks = run_doctor(include_opencode=False)

    output = format_checks(checks)
    assert "OPENCODE_API_KEY" in output
    assert "dummy-api-key" not in output


if __name__ == "__main__":
    test_doctor_warns_when_no_provider_key()
    test_doctor_reports_provider_key_without_revealing_secret()
    print("doctor tests passed")
