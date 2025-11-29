"""
Document Service
Handles import/export of parts, assets, and documentation
"""

import os
import csv
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from io import StringIO, BytesIO
import zipfile

# Import with error handling
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.services.media_service import media_service

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for document import/export operations"""
    
    def __init__(self):
        self.export_dir = "app/static/exports"
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Supported formats
        self.import_formats = {'.csv', '.xlsx', '.json'}
        self.export_formats = {'.csv', '.xlsx', '.json', '.pdf'}

    async def export_parts_catalog(
        self, 
        parts_data: List[Dict[str, Any]], 
        format: str = "csv",
        include_media: bool = False
    ) -> Dict[str, Any]:
        """
        Export parts catalog to various formats
        
        Args:
            parts_data: List of parts dictionaries
            format: Export format (csv, xlsx, json, pdf)
            include_media: Whether to include media files in export
            
        Returns:
            Dict with export info and file path
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"parts_catalog_{timestamp}"
            
            if format.lower() == "csv":
                return await self._export_to_csv(parts_data, base_filename, "parts")
            elif format.lower() == "xlsx" and PANDAS_AVAILABLE:
                return await self._export_to_excel(parts_data, base_filename, "parts")
            elif format.lower() == "json":
                return await self._export_to_json(parts_data, base_filename, "parts")
            elif format.lower() == "pdf" and REPORTLAB_AVAILABLE:
                return await self._export_to_pdf(parts_data, base_filename, "parts")
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise Exception(f"Export failed: {str(e)}")

    async def export_assets_list(
        self, 
        assets_data: List[Dict[str, Any]], 
        format: str = "csv"
    ) -> Dict[str, Any]:
        """Export assets list to specified format"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"assets_list_{timestamp}"
            
            if format.lower() == "csv":
                return await self._export_to_csv(assets_data, base_filename, "assets")
            elif format.lower() == "xlsx" and PANDAS_AVAILABLE:
                return await self._export_to_excel(assets_data, base_filename, "assets")
            elif format.lower() == "json":
                return await self._export_to_json(assets_data, base_filename, "assets")
            elif format.lower() == "pdf" and REPORTLAB_AVAILABLE:
                return await self._export_to_pdf(assets_data, base_filename, "assets")
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Assets export error: {e}")
            raise Exception(f"Assets export failed: {str(e)}")

    async def import_parts_catalog(
        self, 
        file_data: bytes, 
        filename: str, 
        mapping: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Import parts from file
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            mapping: Column mapping for import
            
        Returns:
            Dict with import results
        """
        try:
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext == ".csv":
                return await self._import_from_csv(file_data, mapping, "parts")
            elif file_ext in [".xlsx", ".xls"] and PANDAS_AVAILABLE:
                return await self._import_from_excel(file_data, mapping, "parts")
            elif file_ext == ".json":
                return await self._import_from_json(file_data, mapping, "parts")
            else:
                raise ValueError(f"Unsupported import format: {file_ext}")
                
        except Exception as e:
            logger.error(f"Import error: {e}")
            raise Exception(f"Import failed: {str(e)}")

    async def import_assets_list(
        self, 
        file_data: bytes, 
        filename: str, 
        mapping: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Import assets from file"""
        try:
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext == ".csv":
                return await self._import_from_csv(file_data, mapping, "assets")
            elif file_ext in [".xlsx", ".xls"] and PANDAS_AVAILABLE:
                return await self._import_from_excel(file_data, mapping, "assets")
            elif file_ext == ".json":
                return await self._import_from_json(file_data, mapping, "assets")
            else:
                raise ValueError(f"Unsupported import format: {file_ext}")
                
        except Exception as e:
            logger.error(f"Assets import error: {e}")
            raise Exception(f"Assets import failed: {str(e)}")

    async def _export_to_csv(
        self, 
        data: List[Dict[str, Any]], 
        filename: str, 
        data_type: str
    ) -> Dict[str, Any]:
        """Export data to CSV format"""
        file_path = os.path.join(self.export_dir, f"{filename}.csv")
        
        if not data:
            raise ValueError("No data to export")
        
        # Get all unique keys from all records
        all_keys = set()
        for record in data:
            all_keys.update(record.keys())
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(data)
        
        return {
            "export_id": str(uuid.uuid4()),
            "format": "csv",
            "file_path": file_path,
            "url": f"/static/exports/{filename}.csv",
            "data_type": data_type,
            "record_count": len(data),
            "exported_at": datetime.now().isoformat(),
            "file_size": os.path.getsize(file_path)
        }

    async def _export_to_excel(
        self, 
        data: List[Dict[str, Any]], 
        filename: str, 
        data_type: str
    ) -> Dict[str, Any]:
        """Export data to Excel format"""
        if not PANDAS_AVAILABLE:
            raise Exception("Pandas not available for Excel export")
        
        file_path = os.path.join(self.export_dir, f"{filename}.xlsx")
        
        df = pd.DataFrame(data)
        
        # Create Excel writer with formatting
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=data_type.title(), index=False)
            
            # Get the workbook and worksheet for formatting
            workbook = writer.book
            worksheet = writer.sheets[data_type.title()]
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_name = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_name].width = adjusted_width
        
        return {
            "export_id": str(uuid.uuid4()),
            "format": "xlsx",
            "file_path": file_path,
            "url": f"/static/exports/{filename}.xlsx",
            "data_type": data_type,
            "record_count": len(data),
            "exported_at": datetime.now().isoformat(),
            "file_size": os.path.getsize(file_path)
        }

    async def _export_to_json(
        self, 
        data: List[Dict[str, Any]], 
        filename: str, 
        data_type: str
    ) -> Dict[str, Any]:
        """Export data to JSON format"""
        file_path = os.path.join(self.export_dir, f"{filename}.json")
        
        export_data = {
            "export_info": {
                "data_type": data_type,
                "exported_at": datetime.now().isoformat(),
                "record_count": len(data),
                "version": "1.0"
            },
            "data": data
        }
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        return {
            "export_id": str(uuid.uuid4()),
            "format": "json",
            "file_path": file_path,
            "url": f"/static/exports/{filename}.json",
            "data_type": data_type,
            "record_count": len(data),
            "exported_at": datetime.now().isoformat(),
            "file_size": os.path.getsize(file_path)
        }

    async def _export_to_pdf(
        self, 
        data: List[Dict[str, Any]], 
        filename: str, 
        data_type: str
    ) -> Dict[str, Any]:
        """Export data to PDF format"""
        if not REPORTLAB_AVAILABLE:
            raise Exception("ReportLab not available for PDF export")
        
        file_path = os.path.join(self.export_dir, f"{filename}.pdf")
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"{data_type.title()} Catalog", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Export info
        info_text = f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Records: {len(data)}"
        info = Paragraph(info_text, styles['Normal'])
        story.append(info)
        story.append(Spacer(1, 12))
        
        if data:
            # Create table data
            headers = list(data[0].keys())
            table_data = [headers]
            
            for record in data:
                row = [str(record.get(key, '')) for key in headers]
                table_data.append(row)
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            story.append(table)
        
        doc.build(story)
        
        return {
            "export_id": str(uuid.uuid4()),
            "format": "pdf",
            "file_path": file_path,
            "url": f"/static/exports/{filename}.pdf",
            "data_type": data_type,
            "record_count": len(data),
            "exported_at": datetime.now().isoformat(),
            "file_size": os.path.getsize(file_path)
        }

    async def _import_from_csv(
        self, 
        file_data: bytes, 
        mapping: Dict[str, str], 
        data_type: str
    ) -> Dict[str, Any]:
        """Import data from CSV"""
        content = file_data.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(content))
        
        imported_records = []
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
            try:
                # Apply column mapping if provided
                if mapping:
                    mapped_row = {}
                    for csv_col, app_col in mapping.items():
                        if csv_col in row:
                            mapped_row[app_col] = row[csv_col]
                    row = mapped_row
                
                imported_records.append(row)
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return {
            "import_id": str(uuid.uuid4()),
            "format": "csv",
            "data_type": data_type,
            "imported_records": imported_records,
            "record_count": len(imported_records),
            "error_count": len(errors),
            "errors": errors,
            "imported_at": datetime.now().isoformat()
        }

    async def _import_from_excel(
        self, 
        file_data: bytes, 
        mapping: Dict[str, str], 
        data_type: str
    ) -> Dict[str, Any]:
        """Import data from Excel"""
        if not PANDAS_AVAILABLE:
            raise Exception("Pandas not available for Excel import")
        
        df = pd.read_excel(BytesIO(file_data))
        
        # Apply column mapping if provided
        if mapping:
            df = df.rename(columns=mapping)
        
        # Convert to list of dicts
        imported_records = df.to_dict('records')
        
        # Convert NaN values to None
        for record in imported_records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        return {
            "import_id": str(uuid.uuid4()),
            "format": "xlsx",
            "data_type": data_type,
            "imported_records": imported_records,
            "record_count": len(imported_records),
            "error_count": 0,
            "errors": [],
            "imported_at": datetime.now().isoformat()
        }

    async def _import_from_json(
        self, 
        file_data: bytes, 
        mapping: Dict[str, str], 
        data_type: str
    ) -> Dict[str, Any]:
        """Import data from JSON"""
        content = file_data.decode('utf-8')
        json_data = json.loads(content)
        
        # Handle different JSON structures
        if isinstance(json_data, list):
            imported_records = json_data
        elif isinstance(json_data, dict):
            if 'data' in json_data:
                imported_records = json_data['data']
            else:
                imported_records = [json_data]
        else:
            raise ValueError("Invalid JSON structure")
        
        # Apply column mapping if provided
        if mapping:
            mapped_records = []
            for record in imported_records:
                mapped_record = {}
                for json_key, app_key in mapping.items():
                    if json_key in record:
                        mapped_record[app_key] = record[json_key]
                mapped_records.append(mapped_record)
            imported_records = mapped_records
        
        return {
            "import_id": str(uuid.uuid4()),
            "format": "json",
            "data_type": data_type,
            "imported_records": imported_records,
            "record_count": len(imported_records),
            "error_count": 0,
            "errors": [],
            "imported_at": datetime.now().isoformat()
        }

    def get_import_template(self, data_type: str, format: str = "csv") -> Dict[str, Any]:
        """
        Generate import template for parts or assets
        
        Returns:
            Dict with template info and download URL
        """
        templates = {
            "parts": {
                "part_number": "ABC123",
                "part_name": "Example Part",
                "category": "Mechanical",
                "description": "Part description",
                "unit_cost": "25.99",
                "min_stock": "5",
                "current_stock": "10",
                "supplier": "ACME Parts",
                "location": "Warehouse A-1"
            },
            "assets": {
                "asset_id": "ASSET001",
                "asset_name": "Example Machine",
                "category": "Production Equipment",
                "model": "ABC-2000",
                "manufacturer": "MachCorp",
                "serial_number": "SN123456",
                "location": "Factory Floor",
                "status": "Active",
                "purchase_date": "2023-01-15"
            }
        }
        
        template_data = templates.get(data_type, {})
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{data_type}_import_template_{timestamp}.{format}"
        
        # Create template file
        file_path = os.path.join(self.export_dir, filename)
        
        if format == "csv":
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                if template_data:
                    writer = csv.DictWriter(csvfile, fieldnames=template_data.keys())
                    writer.writeheader()
                    writer.writerow(template_data)
        elif format == "json":
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump([template_data], jsonfile, indent=2)
        
        return {
            "template_type": data_type,
            "format": format,
            "file_path": file_path,
            "url": f"/static/exports/{filename}",
            "generated_at": datetime.now().isoformat()
        }

# Global document service instance
document_service = DocumentService()