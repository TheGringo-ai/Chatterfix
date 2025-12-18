"""
Export Service for ChatterFix CMMS
Provides PDF and Excel export functionality for reports and analytics
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.core.firestore_db import get_firestore_manager
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting reports to PDF and Excel formats"""

    def __init__(self):
        self.supported_formats = ["pdf", "excel", "csv", "json"]
        self.firestore_manager = get_firestore_manager()

    async def export_kpi_report(self, format: str, days: int = 30) -> Dict[str, Any]:
        """
        Export KPI report in the specified format
        Returns the file content and metadata
        """
        try:
            kpi_data = await analytics_service.get_kpi_summary(days)
            if format == "json":
                return self._export_json(kpi_data, "kpi_report")
            elif format == "csv":
                return self._export_kpi_csv(kpi_data)
            elif format == "excel":
                return self._export_kpi_excel(kpi_data)
            elif format == "pdf":
                return self._export_kpi_pdf(kpi_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise

    async def export_work_orders(
        self, format: str, filters: Dict = None
    ) -> Dict[str, Any]:
        """Export work orders report"""
        work_orders = await self.firestore_manager.get_collection(
            "work_orders", order_by="-created_date"
        )
        if format == "json":
            return self._export_json(work_orders, "work_orders")
        elif format == "csv":
            return self._export_list_csv(work_orders, "work_orders")
        elif format == "excel":
            return self._export_list_excel(work_orders, "work_orders")
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def export_assets(self, format: str, filters: Dict = None) -> Dict[str, Any]:
        """Export assets report"""
        assets = await self.firestore_manager.get_collection("assets", order_by="name")
        if format == "json":
            return self._export_json(assets, "assets")
        elif format == "csv":
            return self._export_list_csv(assets, "assets")
        elif format == "excel":
            return self._export_list_excel(assets, "assets")
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def export_maintenance_history(
        self, format: str, days: int = 30
    ) -> Dict[str, Any]:
        """Export maintenance history report"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        history = await self.firestore_manager.get_collection(
            "maintenance_history",
            filters=[{"field": "created_date", "operator": ">=", "value": start_date}],
            order_by="-created_date",
        )
        if format == "json":
            return self._export_json(history, "maintenance_history")
        elif format == "csv":
            return self._export_list_csv(history, "maintenance_history")
        elif format == "excel":
            return self._export_list_excel(history, "maintenance_history")
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, data: Any, filename: str) -> Dict[str, Any]:
        """Export data as JSON"""
        content = json.dumps(data, indent=2, default=str)
        return {
            "content": content,
            "filename": f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "content_type": "application/json",
        }

    # Other export helper methods (_export_kpi_csv, _export_list_csv, etc.) remain the same
    # as they already operate on dictionaries and lists of dictionaries.

    def _export_kpi_csv(self, kpi_data: Dict) -> Dict[str, Any]:
        """Export KPI data as CSV"""
        lines = []

        # Header
        lines.append("KPI Report - ChatterFix CMMS")
        lines.append(
            f"Generated: {kpi_data.get('generated_at', datetime.now().isoformat())}"
        )
        lines.append(f"Period: {kpi_data.get('period_days', 30)} days")
        lines.append("")

        # MTTR Section
        lines.append("Mean Time To Repair (MTTR)")
        mttr = kpi_data.get("mttr", {})
        lines.append(f"Value,{mttr.get('value', 0)},{mttr.get('unit', 'hours')}")
        lines.append(f"Total Repairs,{mttr.get('total_repairs', 0)}")
        lines.append(f"Status,{mttr.get('status', 'unknown')}")
        lines.append("")

        # MTBF Section
        lines.append("Mean Time Between Failures (MTBF)")
        mtbf = kpi_data.get("mtbf", {})
        lines.append(f"Value,{mtbf.get('value', 0)},{mtbf.get('unit', 'hours')}")
        lines.append(f"Failure Count,{mtbf.get('failure_count', 0)}")
        lines.append(f"Status,{mtbf.get('status', 'unknown')}")
        lines.append("")

        # Asset Utilization Section
        lines.append("Asset Utilization")
        util = kpi_data.get("asset_utilization", {})
        lines.append(f"Average Utilization,{util.get('average_utilization', 0)}%")
        lines.append(f"Active Assets,{util.get('active_assets', 0)}")
        lines.append(f"Total Assets,{util.get('total_assets', 0)}")
        lines.append("")

        # Cost Tracking Section
        lines.append("Cost Tracking")
        cost = kpi_data.get("cost_tracking", {})
        lines.append(
            f"Total Cost,{cost.get('total_cost', 0)},{cost.get('currency', 'USD')}"
        )
        lines.append(f"Labor Cost,{cost.get('labor_cost', 0)}")
        lines.append(f"Parts Cost,{cost.get('parts_cost', 0)}")
        lines.append("")

        # Work Order Metrics Section
        lines.append("Work Order Metrics")
        wo = kpi_data.get("work_order_metrics", {})
        lines.append(f"Total Created,{wo.get('total_created', 0)}")
        lines.append(f"Completion Rate,{wo.get('completion_rate', 0)}%")
        lines.append(f"Overdue,{wo.get('overdue_count', 0)}")
        lines.append("")

        # Compliance Metrics Section
        lines.append("Compliance Metrics")
        comp = kpi_data.get("compliance_metrics", {})
        lines.append(f"PM Compliance Rate,{comp.get('pm_compliance_rate', 0)}%")
        lines.append(
            f"Training Compliance Rate,{comp.get('training_compliance_rate', 0)}%"
        )
        lines.append(f"Overall Compliance,{comp.get('overall_compliance', 0)}%")

        content = "\n".join(lines)

        return {
            "content": content,
            "filename": f"kpi_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "content_type": "text/csv",
            "size": len(content),
        }

    def _export_list_csv(self, data: List[Dict], filename: str) -> Dict[str, Any]:
        """Export list data as CSV"""
        if not data:
            return {
                "content": "No data available",
                "filename": f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "content_type": "text/csv",
                "size": 0,
            }

        # Get all unique keys from the data
        headers = set()
        for item in data:
            headers.update(item.keys())
        headers = sorted(list(headers))

        lines = []
        lines.append(",".join(headers))

        for item in data:
            row = []
            for header in headers:
                value = item.get(header, "")
                # Handle special characters in CSV
                if isinstance(value, str) and (
                    "," in value or '"' in value or "\n" in value
                ):
                    value = '"{}"'.format(value.replace('"', '""'))
                row.append(str(value) if value is not None else "")
            lines.append(",".join(row))

        content = "\n".join(lines)

        return {
            "content": content,
            "filename": f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "content_type": "text/csv",
            "size": len(content),
        }

    def _export_kpi_excel(self, kpi_data: Dict) -> Dict[str, Any]:
        """
        Export KPI data as Excel format
        Uses simple XML-based Excel format for compatibility without openpyxl
        """
        # Create simple HTML table that Excel can read
        html_content = self._create_excel_html(kpi_data)

        return {
            "content": html_content,
            "filename": f"kpi_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls",
            "content_type": "application/vnd.ms-excel",
            "size": len(html_content),
        }

    def _create_excel_html(self, kpi_data: Dict) -> str:
        """Create HTML table for Excel export"""
        html = (
            """<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<style>
    table { border-collapse: collapse; }
    th, td { border: 1px solid #000; padding: 5px; }
    th { background-color: #4a90e2; color: white; }
    .section-header { background-color: #e0e0e0; font-weight: bold; }
    .good { background-color: #90ee90; }
    .warning { background-color: #ffd700; }
    .critical { background-color: #ff6b6b; }
</style>
</head>
<body>
<table>
    <tr><th colspan="3">ChatterFix CMMS - KPI Report</th></tr>
    <tr><td colspan="3">Generated: """
            + str(kpi_data.get("generated_at", ""))
            + """</td></tr>
    <tr><td colspan="3">Period: """
            + str(kpi_data.get("period_days", 30))
            + """ days</td></tr>
    <tr><td colspan="3"></td></tr>
"""
        )

        # MTTR Section
        mttr = kpi_data.get("mttr", {})
        html += f"""
    <tr class="section-header"><td colspan="3">Mean Time To Repair (MTTR)</td></tr>
    <tr><td>Value</td><td>{mttr.get('value', 0)}</td><td>{mttr.get('unit', 'hours')}</td></tr>
    <tr><td>Total Repairs</td><td colspan="2">{mttr.get('total_repairs', 0)}</td></tr>
    <tr><td>Status</td><td colspan="2" class="{mttr.get('status', '')}">{mttr.get('status', 'unknown')}</td></tr>
    <tr><td colspan="3"></td></tr>
"""

        # MTBF Section
        mtbf = kpi_data.get("mtbf", {})
        html += f"""
    <tr class="section-header"><td colspan="3">Mean Time Between Failures (MTBF)</td></tr>
    <tr><td>Value</td><td>{mtbf.get('value', 0)}</td><td>{mtbf.get('unit', 'hours')}</td></tr>
    <tr><td>Failure Count</td><td colspan="2">{mtbf.get('failure_count', 0)}</td></tr>
    <tr><td>Status</td><td colspan="2" class="{mtbf.get('status', '')}">{mtbf.get('status', 'unknown')}</td></tr>
    <tr><td colspan="3"></td></tr>
"""

        # Asset Utilization Section
        util = kpi_data.get("asset_utilization", {})
        html += f"""
    <tr class="section-header"><td colspan="3">Asset Utilization</td></tr>
    <tr><td>Average Utilization</td><td colspan="2">{util.get('average_utilization', 0)}%</td></tr>
    <tr><td>Active Assets</td><td colspan="2">{util.get('active_assets', 0)}</td></tr>
    <tr><td>Total Assets</td><td colspan="2">{util.get('total_assets', 0)}</td></tr>
    <tr><td colspan="3"></td></tr>
"""

        # Cost Tracking Section
        cost = kpi_data.get("cost_tracking", {})
        html += f"""
    <tr class="section-header"><td colspan="3">Cost Tracking</td></tr>
    <tr><td>Total Cost</td><td>{cost.get('total_cost', 0)}</td><td>{cost.get('currency', 'USD')}</td></tr>
    <tr><td>Labor Cost</td><td colspan="2">{cost.get('labor_cost', 0)}</td></tr>
    <tr><td>Parts Cost</td><td colspan="2">{cost.get('parts_cost', 0)}</td></tr>
    <tr><td colspan="3"></td></tr>
"""

        # Work Order Metrics Section
        wo = kpi_data.get("work_order_metrics", {})
        html += f"""
    <tr class="section-header"><td colspan="3">Work Order Metrics</td></tr>
    <tr><td>Total Created</td><td colspan="2">{wo.get('total_created', 0)}</td></tr>
    <tr><td>Completion Rate</td><td colspan="2">{wo.get('completion_rate', 0)}%</td></tr>
    <tr><td>Overdue</td><td colspan="2">{wo.get('overdue_count', 0)}</td></tr>
    <tr><td colspan="3"></td></tr>
"""

        # Compliance Metrics Section
        comp = kpi_data.get("compliance_metrics", {})
        html += f"""
    <tr class="section-header"><td colspan="3">Compliance Metrics</td></tr>
    <tr><td>PM Compliance Rate</td><td colspan="2">{comp.get('pm_compliance_rate', 0)}%</td></tr>
    <tr><td>Training Compliance Rate</td><td colspan="2">{comp.get('training_compliance_rate', 0)}%</td></tr>
    <tr><td>Overall Compliance</td><td colspan="2">{comp.get('overall_compliance', 0)}%</td></tr>
"""

        html += """
</table>
</body>
</html>"""

        return html

    def _export_list_excel(self, data: List[Dict], filename: str) -> Dict[str, Any]:
        """Export list data as Excel format"""
        if not data:
            return {
                "content": "<html><body><table><tr><td>No data available</td></tr></table></body></html>",
                "filename": f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls",
                "content_type": "application/vnd.ms-excel",
                "size": 0,
            }

        # Get all unique keys from the data
        headers = set()
        for item in data:
            headers.update(item.keys())
        headers = sorted(list(headers))

        html = """<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<style>
    table { border-collapse: collapse; }
    th, td { border: 1px solid #000; padding: 5px; }
    th { background-color: #4a90e2; color: white; }
</style>
</head>
<body>
<table>
    <tr>"""

        for header in headers:
            html += f"<th>{header}</th>"
        html += "</tr>"

        for item in data:
            html += "<tr>"
            for header in headers:
                value = item.get(header, "")
                html += f"<td>{value if value is not None else ''}</td>"
            html += "</tr>"

        html += """
</table>
</body>
</html>"""

        return {
            "content": html,
            "filename": f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls",
            "content_type": "application/vnd.ms-excel",
            "size": len(html),
        }

    def _export_kpi_pdf(self, kpi_data: Dict) -> Dict[str, Any]:
        """
        Export KPI data as PDF
        Uses HTML-based PDF generation for simplicity
        """
        # Create HTML content for PDF
        html_content = self._create_pdf_html(kpi_data)

        return {
            "content": html_content,
            "filename": f"kpi_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "content_type": "text/html",
            "size": len(html_content),
            "note": "Print this HTML file to PDF for best results",
        }

    def _create_pdf_html(self, kpi_data: Dict) -> str:
        """Create styled HTML for PDF export"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ChatterFix CMMS - KPI Report</title>
    <style>
        @page {{ size: A4; margin: 20mm; }}
        body {{
            font-family: Arial, sans-serif;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 5px 0 0; opacity: 0.9; }}
        .section {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }}
        .section h2 {{
            color: #667eea;
            margin: 0 0 10px;
            font-size: 18px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }}
        .metric {{
            background: white;
            padding: 10px 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-label {{ color: #666; font-size: 12px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .status-excellent {{ color: #27ae60; }}
        .status-good {{ color: #2ecc71; }}
        .status-warning {{ color: #f39c12; }}
        .status-critical {{ color: #e74c3c; }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 ChatterFix CMMS - KPI Report</h1>
        <p>Generated: {kpi_data.get('generated_at', datetime.now().isoformat())} | Period: {kpi_data.get('period_days', 30)} days</p>
    </div>
"""

        # MTTR Section
        mttr = kpi_data.get("mttr", {})
        html += f"""
    <div class="section">
        <h2>⏱️ Mean Time To Repair (MTTR)</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Average Repair Time</div>
                <div class="metric-value">{mttr.get('value', 0)} {mttr.get('unit', 'hours')}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Repairs</div>
                <div class="metric-value">{mttr.get('total_repairs', 0)}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Status</div>
                <div class="metric-value status-{mttr.get('status', 'unknown')}">{mttr.get('status', 'unknown').upper()}</div>
            </div>
        </div>
    </div>
"""

        # MTBF Section
        mtbf = kpi_data.get("mtbf", {})
        html += f"""
    <div class="section">
        <h2>🔄 Mean Time Between Failures (MTBF)</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Average Time Between Failures</div>
                <div class="metric-value">{mtbf.get('value', 0)} {mtbf.get('unit', 'hours')}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Failures</div>
                <div class="metric-value">{mtbf.get('failure_count', 0)}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Status</div>
                <div class="metric-value status-{mtbf.get('status', 'unknown')}">{mtbf.get('status', 'unknown').upper()}</div>
            </div>
        </div>
    </div>
"""

        # Asset Utilization Section
        util = kpi_data.get("asset_utilization", {})
        html += f"""
    <div class="section">
        <h2>📊 Asset Utilization</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Average Utilization</div>
                <div class="metric-value">{util.get('average_utilization', 0)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Active Assets</div>
                <div class="metric-value">{util.get('active_assets', 0)}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Assets</div>
                <div class="metric-value">{util.get('total_assets', 0)}</div>
            </div>
        </div>
    </div>
"""

        # Cost Tracking Section
        cost = kpi_data.get("cost_tracking", {})
        html += f"""
    <div class="section">
        <h2>💰 Cost Tracking</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Total Maintenance Cost</div>
                <div class="metric-value">${cost.get('total_cost', 0):,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Labor Cost</div>
                <div class="metric-value">${cost.get('labor_cost', 0):,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Parts Cost</div>
                <div class="metric-value">${cost.get('parts_cost', 0):,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Cost per Event</div>
                <div class="metric-value">${cost.get('avg_cost_per_event', 0):,.2f}</div>
            </div>
        </div>
    </div>
"""

        # Work Order Metrics Section
        wo = kpi_data.get("work_order_metrics", {})
        html += f"""
    <div class="section">
        <h2>📋 Work Order Metrics</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Total Created</div>
                <div class="metric-value">{wo.get('total_created', 0)}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Completion Rate</div>
                <div class="metric-value">{wo.get('completion_rate', 0)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Overdue</div>
                <div class="metric-value status-{'critical' if wo.get('overdue_count', 0) > 5 else 'warning' if wo.get('overdue_count', 0) > 0 else 'good'}">{wo.get('overdue_count', 0)}</div>
            </div>
        </div>
    </div>
"""

        # Compliance Metrics Section
        comp = kpi_data.get("compliance_metrics", {})
        html += f"""
    <div class="section">
        <h2>✅ Compliance Metrics</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">PM Compliance Rate</div>
                <div class="metric-value">{comp.get('pm_compliance_rate', 0)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Training Compliance Rate</div>
                <div class="metric-value">{comp.get('training_compliance_rate', 0)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Overall Compliance</div>
                <div class="metric-value">{comp.get('overall_compliance', 0)}%</div>
            </div>
        </div>
    </div>
"""

        html += """
    <div class="footer">
        <p>ChatterFix CMMS - AI-Powered Maintenance Management System</p>
        <p>This report was generated automatically. For questions, contact your system administrator.</p>
    </div>
</body>
</html>"""

        return html


# Global export service instance
export_service = ExportService()
