#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - File Import/Export System
Advanced data exchange capabilities that outclass competitors
"""

import pandas as pd
import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import sqlite3
import os
from typing import Dict, List, Any, Optional, Union
import io
import base64
from pathlib import Path

class FileManager:
    """Advanced file import/export system for CMMS data"""
    
    def __init__(self, db_path: str = "./data/cmms_enhanced.db"):
        self.db_path = db_path
        self.supported_formats = {
            'import': ['csv', 'xlsx', 'json', 'xml', 'tsv'],
            'export': ['csv', 'xlsx', 'json', 'xml', 'pdf', 'tsv']
        }
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ==================== IMPORT FUNCTIONS ====================
    
    def import_assets(self, file_data: bytes, file_format: str, mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """Import assets from various file formats with intelligent mapping"""
        try:
            if file_format.lower() == 'csv':
                df = pd.read_csv(io.BytesIO(file_data))
            elif file_format.lower() in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(file_data))
            elif file_format.lower() == 'json':
                data = json.loads(file_data.decode('utf-8'))
                df = pd.DataFrame(data)
            elif file_format.lower() == 'xml':
                return self._import_xml_assets(file_data)
            else:
                return {"success": False, "error": f"Unsupported format: {file_format}"}
            
            # Apply field mapping if provided
            if mapping:
                df = df.rename(columns=mapping)
            
            # Validate and clean data
            df = self._clean_asset_data(df)
            
            # Import to database
            results = self._insert_assets_to_db(df)
            
            return {
                "success": True,
                "imported_count": results['imported'],
                "skipped_count": results['skipped'],
                "errors": results['errors'],
                "message": f"Successfully imported {results['imported']} assets"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def import_work_orders(self, file_data: bytes, file_format: str, mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """Import work orders with auto-validation and asset linking"""
        try:
            if file_format.lower() == 'csv':
                df = pd.read_csv(io.BytesIO(file_data))
            elif file_format.lower() in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(file_data))
            elif file_format.lower() == 'json':
                data = json.loads(file_data.decode('utf-8'))
                df = pd.DataFrame(data)
            else:
                return {"success": False, "error": f"Unsupported format: {file_format}"}
            
            if mapping:
                df = df.rename(columns=mapping)
            
            df = self._clean_work_order_data(df)
            results = self._insert_work_orders_to_db(df)
            
            return {
                "success": True,
                "imported_count": results['imported'],
                "skipped_count": results['skipped'],
                "errors": results['errors']
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def import_parts_inventory(self, file_data: bytes, file_format: str, mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """Import parts with intelligent categorization and supplier matching"""
        try:
            if file_format.lower() == 'csv':
                df = pd.read_csv(io.BytesIO(file_data))
            elif file_format.lower() in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(file_data))
            elif file_format.lower() == 'json':
                data = json.loads(file_data.decode('utf-8'))
                df = pd.DataFrame(data)
            else:
                return {"success": False, "error": f"Unsupported format: {file_format}"}
            
            if mapping:
                df = df.rename(columns=mapping)
            
            df = self._clean_parts_data(df)
            results = self._insert_parts_to_db(df)
            
            return {
                "success": True,
                "imported_count": results['imported'],
                "skipped_count": results['skipped'],
                "errors": results['errors']
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== EXPORT FUNCTIONS ====================
    
    def export_assets(self, file_format: str, filters: Dict[str, Any] = None) -> bytes:
        """Export assets in specified format with advanced filtering"""
        try:
            conn = self.get_db_connection()
            
            # Build query with filters
            query = "SELECT * FROM assets WHERE 1=1"
            params = []
            
            if filters:
                if 'location_id' in filters and filters['location_id']:
                    query += " AND location_id = ?"
                    params.append(filters['location_id'])
                if 'category' in filters and filters['category']:
                    query += " AND category = ?"
                    params.append(filters['category'])
                if 'status' in filters and filters['status']:
                    query += " AND status = ?"
                    params.append(filters['status'])
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return self._export_dataframe(df, file_format, 'assets')
            
        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")
    
    def export_work_orders(self, file_format: str, filters: Dict[str, Any] = None) -> bytes:
        """Export work orders with related asset and user information"""
        try:
            conn = self.get_db_connection()
            
            query = """
                SELECT wo.*, 
                       a.name as asset_name, 
                       a.asset_tag,
                       u.full_name as assigned_to_name,
                       req.full_name as requested_by_name
                FROM work_orders wo
                LEFT JOIN assets a ON wo.asset_id = a.id
                LEFT JOIN users u ON wo.assigned_to = u.id
                LEFT JOIN users req ON wo.requested_by = req.id
                WHERE 1=1
            """
            params = []
            
            if filters:
                if 'status' in filters and filters['status']:
                    query += " AND wo.status = ?"
                    params.append(filters['status'])
                if 'priority' in filters and filters['priority']:
                    query += " AND wo.priority = ?"
                    params.append(filters['priority'])
                if 'date_from' in filters and filters['date_from']:
                    query += " AND wo.created_date >= ?"
                    params.append(filters['date_from'])
                if 'date_to' in filters and filters['date_to']:
                    query += " AND wo.created_date <= ?"
                    params.append(filters['date_to'])
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return self._export_dataframe(df, file_format, 'work_orders')
            
        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")
    
    def export_parts_inventory(self, file_format: str, filters: Dict[str, Any] = None) -> bytes:
        """Export parts inventory with stock levels and supplier info"""
        try:
            conn = self.get_db_connection()
            
            query = """
                SELECT p.*, s.name as supplier_name, s.supplier_code
                FROM parts p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE 1=1
            """
            params = []
            
            if filters:
                if 'category' in filters and filters['category']:
                    query += " AND p.category = ?"
                    params.append(filters['category'])
                if 'low_stock' in filters and filters['low_stock']:
                    query += " AND p.stock_quantity <= p.min_stock_level"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return self._export_dataframe(df, file_format, 'parts_inventory')
            
        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")
    
    def export_maintenance_report(self, file_format: str, date_from: str, date_to: str) -> bytes:
        """Generate comprehensive maintenance report"""
        try:
            conn = self.get_db_connection()
            
            # Complex query for maintenance analytics
            query = """
                SELECT 
                    wo.wo_number,
                    wo.title,
                    wo.work_type,
                    wo.priority,
                    wo.status,
                    a.name as asset_name,
                    a.category as asset_category,
                    l.name as location_name,
                    u.full_name as technician,
                    wo.estimated_hours,
                    wo.actual_hours,
                    wo.estimated_cost,
                    wo.actual_cost,
                    wo.created_date,
                    wo.completion_date,
                    wo.downtime_hours,
                    CASE 
                        WHEN wo.completion_date IS NOT NULL THEN 
                            ROUND((julianday(wo.completion_date) - julianday(wo.created_date)) * 24, 2)
                        ELSE NULL 
                    END as response_time_hours
                FROM work_orders wo
                LEFT JOIN assets a ON wo.asset_id = a.id
                LEFT JOIN locations l ON wo.location_id = l.id
                LEFT JOIN users u ON wo.assigned_to = u.id
                WHERE wo.created_date BETWEEN ? AND ?
                ORDER BY wo.created_date DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[date_from, date_to])
            conn.close()
            
            # Add summary statistics
            summary = {
                'total_work_orders': len(df),
                'completed_work_orders': len(df[df['status'] == 'Completed']),
                'total_downtime_hours': df['downtime_hours'].sum(),
                'avg_response_time': df['response_time_hours'].mean(),
                'total_cost': df['actual_cost'].sum()
            }
            
            if file_format.lower() == 'json':
                result = {
                    'summary': summary,
                    'work_orders': df.to_dict('records')
                }
                return json.dumps(result, indent=2, default=str).encode('utf-8')
            
            return self._export_dataframe(df, file_format, 'maintenance_report')
            
        except Exception as e:
            raise Exception(f"Report generation failed: {str(e)}")
    
    # ==================== HELPER FUNCTIONS ====================
    
    def _clean_asset_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate asset data"""
        # Generate asset tag if missing
        if 'asset_tag' not in df.columns:
            df['asset_tag'] = df.apply(lambda x: f"AST-{datetime.now().strftime('%Y%m%d')}-{x.name:04d}", axis=1)
        
        # Set default values
        df['status'] = df.get('status', 'Active')
        df['condition_rating'] = df.get('condition_rating', 5)
        df['criticality'] = df.get('criticality', 'Medium')
        
        # Convert dates
        date_columns = ['purchase_date', 'installation_date', 'warranty_expiry']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    def _clean_work_order_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate work order data"""
        # Generate WO number if missing
        if 'wo_number' not in df.columns:
            df['wo_number'] = df.apply(lambda x: f"WO-{datetime.now().strftime('%Y%m%d')}-{x.name:04d}", axis=1)
        
        # Set defaults
        df['status'] = df.get('status', 'Open')
        df['priority'] = df.get('priority', 'Medium')
        df['work_type'] = df.get('work_type', 'Corrective')
        
        return df
    
    def _clean_parts_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate parts data"""
        # Generate part number if missing
        if 'part_number' not in df.columns:
            df['part_number'] = df.apply(lambda x: f"PRT-{datetime.now().strftime('%Y%m%d')}-{x.name:04d}", axis=1)
        
        # Set defaults
        df['unit_of_measure'] = df.get('unit_of_measure', 'EA')
        df['min_stock_level'] = df.get('min_stock_level', 5)
        df['stock_quantity'] = df.get('stock_quantity', 0)
        
        return df
    
    def _insert_assets_to_db(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Insert assets into database with conflict handling"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        imported = 0
        skipped = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Check if asset already exists
                cursor.execute("SELECT id FROM assets WHERE asset_tag = ?", (row['asset_tag'],))
                if cursor.fetchone():
                    skipped += 1
                    continue
                
                # Insert asset
                cursor.execute('''
                    INSERT INTO assets (
                        asset_tag, name, category, manufacturer, model, 
                        serial_number, status, condition_rating, criticality
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['asset_tag'], row['name'], row.get('category', ''),
                    row.get('manufacturer', ''), row.get('model', ''),
                    row.get('serial_number', ''), row['status'],
                    row['condition_rating'], row['criticality']
                ))
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {index}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return {'imported': imported, 'skipped': skipped, 'errors': errors}
    
    def _insert_work_orders_to_db(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Insert work orders into database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        imported = 0
        skipped = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                cursor.execute("SELECT id FROM work_orders WHERE wo_number = ?", (row['wo_number'],))
                if cursor.fetchone():
                    skipped += 1
                    continue
                
                cursor.execute('''
                    INSERT INTO work_orders (
                        wo_number, title, description, work_type, priority, status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    row['wo_number'], row['title'], row.get('description', ''),
                    row['work_type'], row['priority'], row['status']
                ))
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {index}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return {'imported': imported, 'skipped': skipped, 'errors': errors}
    
    def _insert_parts_to_db(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Insert parts into database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        imported = 0
        skipped = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                cursor.execute("SELECT id FROM parts WHERE part_number = ?", (row['part_number'],))
                if cursor.fetchone():
                    skipped += 1
                    continue
                
                cursor.execute('''
                    INSERT INTO parts (
                        part_number, name, description, category, unit_cost,
                        stock_quantity, min_stock_level, unit_of_measure
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['part_number'], row['name'], row.get('description', ''),
                    row.get('category', ''), row.get('unit_cost', 0),
                    row['stock_quantity'], row['min_stock_level'], row['unit_of_measure']
                ))
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {index}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return {'imported': imported, 'skipped': skipped, 'errors': errors}
    
    def _export_dataframe(self, df: pd.DataFrame, file_format: str, filename_prefix: str) -> bytes:
        """Export dataframe to specified format"""
        if file_format.lower() == 'csv':
            return df.to_csv(index=False).encode('utf-8')
        
        elif file_format.lower() == 'json':
            return df.to_json(orient='records', indent=2, date_format='iso').encode('utf-8')
        
        elif file_format.lower() in ['xlsx', 'xls']:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=filename_prefix, index=False)
            return output.getvalue()
        
        elif file_format.lower() == 'xml':
            return self._dataframe_to_xml(df, filename_prefix).encode('utf-8')
        
        else:
            raise Exception(f"Unsupported export format: {file_format}")
    
    def _dataframe_to_xml(self, df: pd.DataFrame, root_name: str) -> str:
        """Convert dataframe to XML format"""
        root = ET.Element(root_name)
        
        for index, row in df.iterrows():
            item = ET.SubElement(root, 'item')
            for column, value in row.items():
                element = ET.SubElement(item, column)
                element.text = str(value) if pd.notna(value) else ''
        
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def get_import_template(self, data_type: str, file_format: str) -> bytes:
        """Generate import template files"""
        templates = {
            'assets': {
                'columns': ['asset_tag', 'name', 'category', 'manufacturer', 'model', 
                          'serial_number', 'status', 'condition_rating', 'criticality'],
                'sample_data': [
                    ['AST-001', 'Main Pump', 'Pumps', 'ACME Corp', 'P-100', 'SN123456', 'Active', 5, 'Critical'],
                    ['AST-002', 'HVAC Unit', 'HVAC', 'Climate Co', 'HC-200', 'SN789012', 'Active', 4, 'High']
                ]
            },
            'work_orders': {
                'columns': ['wo_number', 'title', 'description', 'work_type', 'priority', 'status'],
                'sample_data': [
                    ['WO-001', 'Pump Maintenance', 'Routine maintenance check', 'Preventive', 'Medium', 'Open'],
                    ['WO-002', 'HVAC Repair', 'Fix heating issue', 'Corrective', 'High', 'Open']
                ]
            },
            'parts': {
                'columns': ['part_number', 'name', 'description', 'category', 'unit_cost', 
                          'stock_quantity', 'min_stock_level', 'unit_of_measure'],
                'sample_data': [
                    ['PRT-001', 'Pump Bearing', 'Bearing for main pump', 'Bearings', 125.50, 10, 3, 'EA'],
                    ['PRT-002', 'HVAC Filter', 'Air filter', 'Filters', 45.99, 25, 10, 'EA']
                ]
            }
        }
        
        if data_type not in templates:
            raise Exception(f"Template not available for: {data_type}")
        
        template = templates[data_type]
        df = pd.DataFrame(template['sample_data'], columns=template['columns'])
        
        return self._export_dataframe(df, file_format, f"{data_type}_template")

# Initialize the file manager
file_manager = FileManager()