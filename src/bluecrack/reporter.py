"""
BlueCrack Report Generator
============================
Generates beautiful, standalone HTML reports with embedded charts,
metrics, found credentials, and attack configuration details.
"""

import html
import json
import time
from typing import Any, Dict, List, Tuple


class ReportGenerator:
    """Generates premium HTML and JSON attack reports."""

    @staticmethod
    def _unpack_cred(cred: Any) -> Tuple[str, str]:
        if isinstance(cred, dict):
            return str(cred.get("username", "")), str(cred.get("password", ""))
        elif isinstance(cred, (list, tuple)) and len(cred) >= 2:
            return str(cred[0]), str(cred[1])
        return str(cred), ""

    @staticmethod
    def generate_html(
        metrics: Dict[str, Any],
        found_creds: List[Any],
        logs: List[str],
        config: Dict[str, Any],
        start_time: float,
        end_time: float,
    ) -> str:
        """Generate a complete standalone HTML report.

        Returns a self-contained HTML document with inline CSS, Chart.js,
        and all attack data embedded.
        """
        elapsed = max(0.0, float(end_time - start_time))
        try:
            attempted = int(metrics.get("attempted", 0) or 0)
            successes = int(metrics.get("successes", 0) or 0)
            failures = int(metrics.get("failures", 0) or 0)
            errors = int(metrics.get("errors", 0) or 0)
            skipped = int(metrics.get("skipped_empty", 0) or 0) + int(
                metrics.get("skipped_solved_user", 0) or 0
            )
        except Exception:
            attempted = successes = failures = errors = skipped = 0

        speed = float(attempted / elapsed) if elapsed > 0 else 0.0
        try:
            start_str = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(start_time)
            )
        except Exception:
            start_str = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            end_str = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(end_time)
            )
        except Exception:
            end_str = time.strftime("%Y-%m-%d %H:%M:%S")

        # Escape all user-provided data
        target = html.escape(str(config.get("target_url", "N/A")))
        threads_val = html.escape(str(config.get("threads", 1)))
        delay_val = html.escape(str(config.get("delay", 0)))
        jitter_val = html.escape(str(config.get("jitter", 0)))
        headless_val = "Yes" if config.get("headless") else "No"
        tor_val = "Enabled" if config.get("use_tor") else "Disabled"

        creds_rows = ""
        for i, cred in enumerate(found_creds, 1):
            u, p = ReportGenerator._unpack_cred(cred)
            eu, ep = html.escape(u), html.escape(p)
            creds_rows += (
                f"<tr><td>{i}</td><td>{eu}</td><td>{ep}</td></tr>\n"
            )

        log_text = html.escape("\n".join(logs[-500:]))  # Last 500 lines

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BlueCrack Report — {start_str}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: 'Inter', sans-serif;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
  color: #e0e0e0;
  min-height: 100vh;
  padding: 2rem;
}}
.container {{ max-width: 1000px; margin: 0 auto; }}
h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;
     background: linear-gradient(135deg, #6c5ce7, #a29bfe);
     -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.subtitle {{ color: #888; margin-bottom: 2rem; }}
.card {{
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}}
.card h2 {{ font-size: 1.1rem; color: #a29bfe; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 1px; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; }}
.stat {{ text-align: center; padding: 1rem; background: rgba(108,92,231,0.1); border-radius: 8px; }}
.stat-value {{ font-size: 1.8rem; font-weight: 700; color: #6c5ce7; }}
.stat-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.25rem; }}
.chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
.chart-box {{ position: relative; height: 250px; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
th {{ color: #a29bfe; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }}
td {{ font-family: 'Courier New', monospace; }}
.success {{ color: #00b894; font-weight: 600; }}
.log-box {{ max-height: 400px; overflow-y: auto; background: rgba(0,0,0,0.3); border-radius: 8px; padding: 1rem;
            font-family: 'Courier New', monospace; font-size: 0.8rem; white-space: pre-wrap; line-height: 1.5; color: #aaa; }}
.footer {{ text-align: center; color: #555; font-size: 0.75rem; margin-top: 2rem; padding-top: 1rem;
           border-top: 1px solid rgba(255,255,255,0.05); }}
.badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }}
.badge-success {{ background: rgba(0,184,148,0.2); color: #00b894; }}
.badge-fail {{ background: rgba(214,48,49,0.2); color: #d63031; }}
@media (max-width: 600px) {{ .chart-row, .stats-grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">
  <h1>🔒 BlueCrack Attack Report</h1>
  <p class="subtitle">Generated {end_str}</p>

  <div class="card">
    <h2>📊 Executive Summary</h2>
    <div class="stats-grid">
      <div class="stat"><div class="stat-value">{attempted}</div><div class="stat-label">Attempted</div></div>
      <div class="stat"><div class="stat-value success">{successes}</div><div class="stat-label">Hits</div></div>
      <div class="stat"><div class="stat-value">{failures}</div><div class="stat-label">Failed</div></div>
      <div class="stat"><div class="stat-value">{errors}</div><div class="stat-label">Errors</div></div>
      <div class="stat"><div class="stat-value">{speed:.1f}</div><div class="stat-label">Speed (att/s)</div></div>
      <div class="stat"><div class="stat-value">{elapsed:.0f}s</div><div class="stat-label">Duration</div></div>
    </div>
  </div>

  <div class="card">
    <h2>📈 Results Distribution</h2>
    <div class="chart-row">
      <div class="chart-box"><canvas id="resultsChart"></canvas></div>
      <div style="display:flex;flex-direction:column;justify-content:center;">
        <p><span class="badge badge-success">Target</span> {target}</p>
        <br>
        <p>Started: {start_str}</p>
        <p>Ended: {end_str}</p>
        <p>Threads: {threads_val}</p>
      </div>
    </div>
  </div>

  {"<div class='card'><h2>🔓 Found Credentials</h2><table><tr><th>#</th><th>Username</th><th>Password</th></tr>" + creds_rows + "</table></div>" if found_creds else "<div class='card'><h2>🔓 Found Credentials</h2><p style='color:#888;'>No credentials found.</p></div>"}

  <div class="card">
    <h2>⚙️ Attack Configuration</h2>
    <table>
      <tr><td>Target URL</td><td>{target}</td></tr>
      <tr><td>Threads</td><td>{threads_val}</td></tr>
      <tr><td>Delay</td><td>{delay_val}s</td></tr>
      <tr><td>Jitter</td><td>{jitter_val}s</td></tr>
      <tr><td>Headless</td><td>{headless_val}</td></tr>
      <tr><td>Tor</td><td>{tor_val}</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>📝 Attack Log (Last 500 lines)</h2>
    <div class="log-box">{log_text}</div>
  </div>

  <div class="footer">
    BlueCrack Report • Generated automatically • {end_str}
  </div>
</div>

<script>
new Chart(document.getElementById('resultsChart'), {{
  type: 'doughnut',
  data: {{
    labels: ['Success', 'Failed', 'Errors', 'Skipped'],
    datasets: [{{ data: [{successes}, {failures}, {errors}, {skipped}],
                  backgroundColor: ['#00b894','#d63031','#fdcb6e','#636e72'],
                  borderWidth: 0 }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false,
             plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#aaa' }} }} }} }}
}});
</script>
</body>
</html>"""

    @staticmethod
    def generate_json(
        metrics: Dict[str, Any],
        found_creds: List[Tuple[str, str]],
        config: Dict[str, Any],
        start_time: float,
        end_time: float,
    ) -> str:
        """Generate a JSON report string."""
        elapsed = max(0.0, float(end_time - start_time))
        try:
            start_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time))
        except Exception:
            start_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            end_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time))
        except Exception:
            end_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        parsed_creds = []
        for c in found_creds:
            u, p = ReportGenerator._unpack_cred(c)
            parsed_creds.append({"username": u, "password": p})

        report = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "target_url": config.get("target_url", ""),
            "start_time": start_str,
            "end_time": end_str,
            "elapsed_seconds": round(elapsed, 1),
            "metrics": dict(metrics),
            "found_credentials": parsed_creds,
            "config": {
                k: v
                for k, v in config.items()
                if k not in (
                    "users", "passwords", "proxies",
                    "webhook_url", "bot_token", "discord_url",
                    "telegram_token", "telegram_chat_id",
                    "api_key", "token", "secret"
                )
            },
        }
        return json.dumps(report, indent=2, default=str)
