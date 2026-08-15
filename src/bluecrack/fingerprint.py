"""
BlueCrack Response & Technology Fingerprinter
================================================
Smart success/failure detection using response similarity analysis,
and automated web technology stack / CSRF token discovery.
"""

import difflib
import hashlib
import re
import threading
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin


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
        """Extract HTML tag skeleton and compute its hash."""
        tags = re.findall(r"</?[a-zA-Z][a-zA-Z0-9]*[^>]*>", body)
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


# ═══════════════════════════════════════════════════════════════════
# TARGET TECHNOLOGY & CSRF DETECTOR
# ═══════════════════════════════════════════════════════════════════

class TechnologyDetector:
    """Fingerprints target web technologies, frameworks, servers, and CSRF mechanisms."""

    SIGNATURES = {
        "frameworks": [
            ("WordPress", [r"wp-content", r"wp-includes", r"xmlrpc\.php", r"wp-login\.php"]),
            ("Django", [r"csrfmiddlewaretoken", r"__admin__", r"django"]),
            ("Laravel", [r"laravel", r"XSRF-TOKEN", r"_token"]),
            ("Next.js", [r"/_next/", r"__NEXT_DATA__"]),
            ("FastAPI", [r"fastapi", r"/docs#/default"]),
            ("Flask", [r"session=", r"werkzeug"]),
            ("Express / Node", [r"express", r"connect\.sid"]),
            ("Ruby on Rails", [r"authenticity_token", r"_rails_"]),
            ("ASP.NET", [r"__VIEWSTATE", r"__EVENTVALIDATION", r"ASP\.NET", r"aspnet"]),
            ("Spring Boot", [r"spring", r"whitelabel error page", r"JSESSIONID"]),
            ("Drupal", [r"Drupal", r"drupal\.js", r"/sites/default/files"]),
            ("Joomla", [r"joomla", r"/media/system/js/"]),
            ("Vue.js", [r"data-v-[a-f0-9]+", r"vue\.js", r"__vue__"]),
            ("React", [r"data-reactroot", r"react-dom", r"_reactListening"]),
            ("Angular", [r"ng-version", r"ng-app", r"_ngcontent"]),
        ],
        "servers": [
            ("Cloudflare", [r"cloudflare", r"__cfduid", r"cf-ray"]),
            ("Nginx", [r"nginx"]),
            ("Apache", [r"apache"]),
            ("LiteSpeed", [r"litespeed"]),
            ("Microsoft-IIS", [r"microsoft-iis"]),
            ("Caddy", [r"caddy"]),
        ],
        "protections": [
            ("Cloudflare Turnstile", [r"challenges\.cloudflare\.com/turnstile", r"cf-turnstile"]),
            ("Google reCAPTCHA", [r"google\.com/recaptcha", r"g-recaptcha"]),
            ("hCaptcha", [r"hcaptcha\.com", r"h-captcha"]),
            ("AWS WAF", [r"awswaf", r"aws-waf-token"]),
            ("Akamai Bot Manager", [r"ak_bmsc", r"akamai"]),
        ]
    }

    CSRF_FIELD_NAMES = [
        "csrf_token",
        "csrf",
        "_token",
        "authenticity_token",
        "__RequestVerificationToken",
        "csrfmiddlewaretoken",
        "anti_forgery_token",
        "_csrf",
        "_csrf_token",
        "token",
    ]

    @classmethod
    def analyze(
        cls,
        url: str,
        body: str = "",
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Analyze page response and headers to detect technologies and form fields.

        Args:
            url: Target URL.
            body: HTML body text.
            headers: Response headers dict.

        Returns:
            Dict containing detected technologies, servers, protections, and discovered form fields.
        """
        headers = headers or {}
        headers_str = " ".join(f"{k}: {v}" for k, v in headers.items())
        combined_text = f"{headers_str}\n{body}"

        detected_frameworks: List[str] = []
        detected_servers: List[str] = []
        detected_protections: List[str] = []

        # 1. Detect Frameworks
        for name, patterns in cls.SIGNATURES["frameworks"]:
            for pat in patterns:
                if re.search(pat, combined_text, re.IGNORECASE):
                    detected_frameworks.append(name)
                    break

        # 2. Detect Servers
        server_hdr = headers.get("Server", "") or headers.get("server", "")
        if server_hdr:
            for name, patterns in cls.SIGNATURES["servers"]:
                for pat in patterns:
                    if re.search(pat, server_hdr, re.IGNORECASE):
                        detected_servers.append(name)
                        break

        if not detected_servers:
            for name, patterns in cls.SIGNATURES["servers"]:
                for pat in patterns:
                    if re.search(pat, combined_text, re.IGNORECASE):
                        detected_servers.append(name)
                        break

        # 3. Detect Protections
        for name, patterns in cls.SIGNATURES["protections"]:
            for pat in patterns:
                if re.search(pat, combined_text, re.IGNORECASE):
                    detected_protections.append(name)
                    break

        # 4. Form Field Discovery
        form_info = cls.extract_form_details(url, body)

        return {
            "url": url,
            "frameworks": list(dict.fromkeys(detected_frameworks)),
            "servers": list(dict.fromkeys(detected_servers)),
            "protections": list(dict.fromkeys(detected_protections)),
            "form": form_info,
        }

    @classmethod
    def extract_form_details(cls, base_url: str, body: str) -> Dict[str, Any]:
        """Extract login form details including action URL, input fields, and CSRF token."""
        result: Dict[str, Any] = {
            "action": base_url,
            "method": "POST",
            "username_field": "username",
            "password_field": "password",
            "csrf_field": None,
            "csrf_value": None,
            "has_login_form": False,
        }

        if not body:
            return result

        # Find form tags
        form_match = re.search(r"<form\b([^>]*)>(.*?)</form>", body, re.IGNORECASE | re.DOTALL)
        form_attrs = form_match.group(1) if form_match else ""
        form_body = form_match.group(2) if form_match else body

        if form_match:
            result["has_login_form"] = True
            action_match = re.search(r'action=["\'](.*?)["\']', form_attrs, re.IGNORECASE)
            if action_match:
                action_val = action_match.group(1).strip()
                result["action"] = urljoin(base_url, action_val) if action_val else base_url

            method_match = re.search(r'method=["\'](.*?)["\']', form_attrs, re.IGNORECASE)
            if method_match:
                result["method"] = method_match.group(1).upper()

        # Extract all input fields
        inputs = re.findall(r"<input\b([^>]*)>", form_body, re.IGNORECASE)
        for inp in inputs:
            type_m = re.search(r'type=["\'](.*?)["\']', inp, re.IGNORECASE)
            name_m = re.search(r'name=["\'](.*?)["\']', inp, re.IGNORECASE)
            val_m = re.search(r'value=["\'](.*?)["\']', inp, re.IGNORECASE)

            inp_type = (type_m.group(1).lower() if type_m else "text").strip()
            inp_name = (name_m.group(1) if name_m else "").strip()
            inp_val = val_m.group(1) if val_m else ""

            if not inp_name:
                continue

            # Password field
            if inp_type == "password" or "pass" in inp_name.lower():
                result["password_field"] = inp_name
                result["has_login_form"] = True

            # Username field
            elif (
                inp_type in ("text", "email")
                and any(k in inp_name.lower() for k in ("user", "usr", "email", "login", "auth", "account", "log"))
            ):
                result["username_field"] = inp_name
                result["has_login_form"] = True

            # CSRF token
            if inp_name.lower() in [k.lower() for k in cls.CSRF_FIELD_NAMES] or "csrf" in inp_name.lower():
                result["csrf_field"] = inp_name
                result["csrf_value"] = inp_val

        return result
