"""Tests for ResponseFingerprinter and TechnologyDetector."""

from bluecrack.fingerprint import ResponseFingerprinter, TechnologyDetector


def test_response_fingerprinter_calibration():
    """Test calibration behavior and baseline additions."""
    rf = ResponseFingerprinter()
    assert not rf.is_calibrated

    # Add baselines
    rf.add_baseline(200, "<html><body>Invalid login</body></html>")
    rf.add_baseline(200, "<html><body>Invalid username or password</body></html>")
    assert not rf.is_calibrated

    rf.add_baseline(200, "<html><body>Wrong credentials</body></html>")
    assert rf.is_calibrated

    # Identical response should not be marked different
    is_diff, score = rf.is_different(200, "<html><body>Invalid login</body></html>")
    assert not is_diff
    assert score < 0.35

    # Completely different response (e.g. 302 redirect with new dashboard structure)
    is_diff, score = rf.is_different(302, "<html><head><title>Dashboard</title></head><body><h1>Welcome Admin</h1></body></html>", url="https://example.com/dashboard")
    assert is_diff
    assert score > 0.35

    # Reset
    rf.reset()
    assert not rf.is_calibrated


def test_technology_detector_frameworks():
    """Test signature detection for WordPress, Django, Laravel, and servers."""
    wp_html = """
    <html>
    <head><link rel="stylesheet" href="/wp-content/themes/twentytwenty/style.css"></head>
    <body>
      <form action="/wp-login.php" method="POST">
        <input type="text" name="log" value="" />
        <input type="password" name="pwd" value="" />
        <input type="hidden" name="csrf_token" value="wp_secret_token_123" />
      </form>
    </body>
    </html>
    """
    analysis = TechnologyDetector.analyze(
        url="https://example.com/wp-login.php",
        body=wp_html,
        headers={"Server": "nginx/1.24.0", "X-Powered-By": "PHP/8.2"},
    )

    assert "WordPress" in analysis["frameworks"]
    assert "Nginx" in analysis["servers"]
    assert analysis["form"]["has_login_form"] is True
    assert analysis["form"]["password_field"] == "pwd"
    assert analysis["form"]["username_field"] == "log"
    assert analysis["form"]["csrf_field"] == "csrf_token"
    assert analysis["form"]["csrf_value"] == "wp_secret_token_123"


def test_technology_detector_django_csrf():
    """Test detection of Django CSRF middleware token."""
    django_html = """
    <form action="/login" method="post">
      <input type="hidden" name="csrfmiddlewaretoken" value="dJ4ng0CsrfT0k3nXYZ123456" />
      <input type="text" name="username" />
      <input type="password" name="password" />
    </form>
    """
    analysis = TechnologyDetector.analyze(
        url="https://example.com/login",
        body=django_html,
        headers={"Server": "gunicorn", "Set-Cookie": "csrftoken=dJ4ng0CsrfT0k3nXYZ123456"},
    )

    assert "Django" in analysis["frameworks"]
    assert analysis["form"]["csrf_field"] == "csrfmiddlewaretoken"
    assert analysis["form"]["csrf_value"] == "dJ4ng0CsrfT0k3nXYZ123456"
