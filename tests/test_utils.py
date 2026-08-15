"""Tests for utilities and wordlist generator helpers."""

import os
import tempfile

from bluecrack.utils import generate_sequence_wordlist, save_json_report


def test_generate_sequence_wordlist():
    """Test generating a numeric sequence wordlist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = os.path.join(tmp_dir, "seq.txt")
        result = generate_sequence_wordlist(
            start=0,
            end=5,
            prefix="pin_",
            suffix="!",
            pad_width=3,
            output_path=out_file,
        )

        assert result == out_file
        assert os.path.exists(out_file)
        with open(out_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f]

        assert lines == ["pin_000!", "pin_001!", "pin_002!", "pin_003!", "pin_004!", "pin_005!"]


def test_save_json_report():
    """Test saving JSON report to disk."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_file = os.path.join(tmp_dir, "report.json")
        save_json_report(
            report_path=report_file,
            target_url="https://test.com",
            metrics={"attempted": 5},
            found_creds=[("admin", "admin")],
            start_time=100.0,
            end_time=105.0,
        )
        assert os.path.exists(report_file)
