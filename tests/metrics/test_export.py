"""Tests for metrics HTML export."""

import os

from archunitpython.metrics.fluentapi.export_utils import ExportOptions, MetricsExporter


class TestMetricsExporter:
    def test_basic_export(self):
        data = {"MethodCount": 5, "FieldCount": 3}
        html = MetricsExporter.export_as_html(data)
        assert "<!DOCTYPE html>" in html
        assert "MethodCount" in html
        assert "FieldCount" in html

    def test_custom_title(self):
        data = {"Metric": "Value"}
        html = MetricsExporter.export_as_html(
            data, ExportOptions(title="My Report")
        )
        assert "My Report" in html

    def test_custom_css(self):
        data = {"Metric": "Value"}
        html = MetricsExporter.export_as_html(
            data, ExportOptions(custom_css="body { color: red; }")
        )
        assert "color: red" in html

    def test_no_timestamp(self):
        data = {"Metric": "Value"}
        html = MetricsExporter.export_as_html(
            data, ExportOptions(include_timestamp=False)
        )
        assert "Generated:" not in html

    def test_file_output(self, tmp_path):
        data = {"MethodCount": 10}
        output = str(tmp_path / "report.html")
        MetricsExporter.export_as_html(data, ExportOptions(output_path=output))
        assert os.path.exists(output)
        with open(output) as f:
            content = f.read()
        assert "MethodCount" in content

    def test_auto_html_extension(self, tmp_path):
        data = {"Test": 1}
        output = str(tmp_path / "report")
        MetricsExporter.export_as_html(data, ExportOptions(output_path=output))
        assert os.path.exists(output + ".html")
