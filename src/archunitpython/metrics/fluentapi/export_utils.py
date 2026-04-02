"""HTML report export for metrics results."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExportOptions:
    """Options for metrics export."""

    output_path: str | None = None
    title: str = "ArchUnitPython Metrics Report"
    include_timestamp: bool = True
    custom_css: str | None = None


class MetricsExporter:
    """Export metrics results as HTML reports."""

    @staticmethod
    def export_as_html(
        data: dict,
        options: ExportOptions | None = None,
    ) -> str:
        """Export metric data as an HTML report.

        Args:
            data: Dictionary of metric results to include.
            options: Export options.

        Returns:
            HTML content as a string. Also writes to file if output_path specified.
        """
        opts = options or ExportOptions()
        timestamp = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if opts.include_timestamp
            else ""
        )

        css = opts.custom_css or _DEFAULT_CSS

        rows = ""
        for key, value in data.items():
            rows += f"      <tr><td>{key}</td><td>{value}</td></tr>\n"

        html = f"""<!DOCTYPE html>
<html>
<head>
  <title>{opts.title}</title>
  <style>{css}</style>
</head>
<body>
  <h1>{opts.title}</h1>
  {f'<p class="timestamp">Generated: {timestamp}</p>' if timestamp else ''}
  <table>
    <thead>
      <tr><th>Metric</th><th>Value</th></tr>
    </thead>
    <tbody>
{rows}    </tbody>
  </table>
</body>
</html>"""

        if opts.output_path:
            path = opts.output_path
            if not path.endswith(".html"):
                path += ".html"
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

        return html


_DEFAULT_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       max-width: 900px; margin: 0 auto; padding: 20px; }
h1 { color: #333; }
.timestamp { color: #666; font-size: 0.9em; }
table { border-collapse: collapse; width: 100%; margin-top: 20px; }
th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
th { background-color: #f5f5f5; font-weight: 600; }
tr:nth-child(even) { background-color: #fafafa; }
"""
