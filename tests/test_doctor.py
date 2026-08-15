"""Tests for system doctor diagnostics."""

from bluecrack.doctor import diagnose, run_doctor


def test_doctor_diagnose():
    """Verify diagnose() returns structured diagnostic results."""
    report = diagnose()
    assert isinstance(report, dict)
    assert "version" in report
    assert "is_healthy" in report
    assert "passed_count" in report
    assert "total_count" in report
    assert "checks" in report
    assert isinstance(report["checks"], list)
    assert len(report["checks"]) >= 5

    # Each check must have name, status (ok|warn|fail), and detail
    for check in report["checks"]:
        assert "name" in check
        assert check["status"] in ("ok", "warn", "fail")
        assert "detail" in check


def test_doctor_run_output(capsys):
    """Verify run_doctor() prints formatted CLI output without throwing exceptions."""
    run_doctor()
    captured = capsys.readouterr()
    assert "Environment Doctor" in captured.out
    assert "Diagnostic Summary" in captured.out
