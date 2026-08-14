"""
BlueCrack Response Fingerprinter
==================================
Smart success/failure detection using response similarity analysis
instead of relying solely on string matching.
"""

import difflib
import hashlib
import re
import threading
from typing import Any, Dict, List, Tuple


class ResponseFingerprinter:
    """Analyzes response patterns to detect success/failure without string matching.

    Collects baseline responses from known-bad logins, then compares
    subsequent responses to detect significant deviations that indicate success.
    """

    def __init__(self) -> None:
        self._baseline_samples: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._calibrated = False
        self._min_samples = 3

    def add_baseline(
        self, status_code: int, body: str, url: str = ""
    ) -> None:
        """Add a known-bad response to the baseline collection.

        Args:
            status_code: HTTP status code.
            body: Response body text.
            url: Final URL after redirects.
        """
        sample = {
            "status_code": status_code,
            "length": len(body),
            "structure_hash": self._compute_structure_hash(body),
            "content_sample": body[:2000],
            "url": url,
        }
        with self._lock:
            self._baseline_samples.append(sample)
            if len(self._baseline_samples) >= self._min_samples:
                self._calibrated = True

    @property
    def is_calibrated(self) -> bool:
        """Check if enough baseline samples have been collected."""
        with self._lock:
            return self._calibrated

    def is_different(
        self, status_code: int, body: str, url: str = ""
    ) -> Tuple[bool, float]:
        """Check if a response differs significantly from the baseline.

        Returns:
            Tuple of (is_different: bool, confidence: float 0.0-1.0).
            Higher confidence means higher likelihood the response is
            genuinely different (potential success).
        """
        if not self._calibrated:
            return False, 0.0

        current = {
            "status_code": status_code,
            "length": len(body),
            "structure_hash": self._compute_structure_hash(body),
            "content_sample": body[:2000],
            "url": url,
        }

        scores: List[float] = []

        with self._lock:
            baselines = list(self._baseline_samples)

        for baseline in baselines:
            score = self._compare(baseline, current)
            scores.append(score)

        # Average difference score across all baselines
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Threshold: >0.35 means significantly different
        is_diff = avg_score > 0.35
        return is_diff, round(avg_score, 3)

    def _compare(
        self, baseline: Dict[str, Any], current: Dict[str, Any]
    ) -> float:
        """Compare a current response against a single baseline sample.

        Returns a difference score from 0.0 (identical) to 1.0 (completely different).
        """
        weights = {
            "status_code": 0.20,
            "length": 0.20,
            "structure": 0.25,
            "content": 0.25,
            "url": 0.10,
        }
        score = 0.0

        # 1. Status code difference
        if baseline["status_code"] != current["status_code"]:
            score += weights["status_code"]

        # 2. Response length deviation (>20% different)
        base_len = max(baseline["length"], 1)
        curr_len = max(current["length"], 1)
        len_ratio = abs(base_len - curr_len) / max(base_len, curr_len)
        if len_ratio > 0.2:
            score += weights["length"] * min(len_ratio, 1.0)

        # 3. Structure hash difference
        if baseline["structure_hash"] != current["structure_hash"]:
            score += weights["structure"]

        # 4. Content similarity (using difflib)
        similarity = difflib.SequenceMatcher(
            None,
            baseline["content_sample"],
            current["content_sample"],
        ).ratio()
        content_diff = 1.0 - similarity
        score += weights["content"] * content_diff

        # 5. URL redirect detection
        if baseline["url"] and current["url"]:
            if baseline["url"] != current["url"]:
                score += weights["url"]

        return min(score, 1.0)

    @staticmethod
    def _compute_structure_hash(body: str) -> str:
        """Extract HTML tag skeleton and compute its hash.

        This captures the structural layout of the page without content,
        making it robust against dynamic text changes.
        """
        # Extract just the HTML tags
        tags = re.findall(r"</?[a-zA-Z][a-zA-Z0-9]*[^>]*>", body)
        # Keep only tag names for skeleton
        skeleton = []
        for tag in tags:
            match = re.match(r"</?([a-zA-Z][a-zA-Z0-9]*)", tag)
            if match:
                skeleton.append(match.group(0).lower())

        skeleton_str = "|".join(skeleton[:200])
        return hashlib.md5(skeleton_str.encode()).hexdigest()

    def reset(self) -> None:
        """Clear all baseline samples and reset calibration."""
        with self._lock:
            self._baseline_samples.clear()
            self._calibrated = False
