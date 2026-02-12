"""
Quality Reporter
Generates HTML and CSV reports from a list of CheckResult objects.
"""

import csv
import os
from datetime import datetime
from typing import List
from checks.sql_checks import CheckResult


def generate_csv_report(results: List[CheckResult], output_path: str) -> str:
    """Write all check results to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "check_id", "check_name", "table", "column",
            "passed", "expected", "actual", "details", "severity"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow(r.to_dict())
    return output_path


def generate_html_report(results: List[CheckResult], output_path: str,
                          run_name: str = "Data Quality Report") -> str:
    """Generate a styled HTML quality report."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = passed / total * 100 if total else 0

    rows_html = ""
    for r in results:
        status_class = "pass" if r.passed else "fail"
        status_text = "✅ PASS" if r.passed else "❌ FAIL"
        rows_html += f"""
        <tr class="{status_class}">
          <td>{r.check_id}</td>
          <td>{r.check_name}</td>
          <td>{r.table}</td>
          <td>{r.column or '—'}</td>
          <td class="badge {status_class}">{status_text}</td>
          <td>{r.expected}</td>
          <td>{r.actual}</td>
          <td>{r.details}</td>
          <td><span class="sev sev-{r.severity.lower()}">{r.severity}</span></td>
        </tr>"""

    severity_badge = "🟢" if pass_rate >= 90 else ("🟡" if pass_rate >= 70 else "🔴")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{run_name}</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 20px; }}
    h1 {{ color: #2c3e50; }}
    .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
    .card {{ background: white; border-radius: 8px; padding: 20px 30px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); text-align: center; }}
    .card .value {{ font-size: 2.5em; font-weight: bold; }}
    .card.total .value {{ color: #3498db; }}
    .card.passed .value {{ color: #27ae60; }}
    .card.failed .value {{ color: #e74c3c; }}
    .card.rate .value {{ color: #8e44ad; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
    th {{ background: #2c3e50; color: white; padding: 12px; text-align: left; font-size: 0.85em; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #ecf0f1; font-size: 0.85em; }}
    tr.pass {{ background: #f0fff4; }}
    tr.fail {{ background: #fff5f5; }}
    .badge.pass {{ color: #27ae60; font-weight: bold; }}
    .badge.fail {{ color: #e74c3c; font-weight: bold; }}
    .sev {{ padding: 2px 8px; border-radius: 10px; font-size: 0.8em; font-weight: bold; }}
    .sev-high {{ background: #fde8e8; color: #c0392b; }}
    .sev-medium {{ background: #fef9e7; color: #d68910; }}
    .sev-low {{ background: #eaf4fb; color: #2471a3; }}
    .footer {{ margin-top: 20px; color: #7f8c8d; font-size: 0.8em; text-align: center; }}
  </style>
</head>
<body>
  <h1>{severity_badge} {run_name}</h1>
  <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

  <div class="summary">
    <div class="card total"><div class="label">Total Checks</div><div class="value">{total}</div></div>
    <div class="card passed"><div class="label">Passed</div><div class="value">{passed}</div></div>
    <div class="card failed"><div class="label">Failed</div><div class="value">{failed}</div></div>
    <div class="card rate"><div class="label">Pass Rate</div><div class="value">{pass_rate:.1f}%</div></div>
  </div>

  <table>
    <thead>
      <tr>
        <th>ID</th><th>Check</th><th>Table</th><th>Column</th>
        <th>Status</th><th>Expected</th><th>Actual</th><th>Details</th><th>Severity</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>

  <div class="footer">
    Imane Moussafir — Data Quality Report | {run_name}
  </div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
