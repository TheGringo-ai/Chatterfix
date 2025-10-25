#!/usr/bin/env python3
"""
TimescaleDB IoT Data Integration for ChatterFix Predictive Intelligence
Handles sensor data ingestion, processing, and real-time analytics
"""

import asyncio
import asyncpg
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import random
from collections import defaultdict
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatterFix TimescaleDB IoT Integration",
    description="Real-time IoT sensor data management and analytics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:REDACTED_DB_PASSWORD@localhost:5432/chatterfix_enterprise")

@dataclass
class SensorReading:
    timestamp: datetime
    tenant_id: str
    sensor_id: str
    asset_id: int
    metric_type: str
    value: float
    unit: str
    quality_score: float = 1.0
    metadata: Dict = None

class SensorDataModel(BaseModel):
    sensor_id: str
    asset_id: int
    metric_type: str
    value: float
    unit: str
    quality_score: Optional[float] = 1.0
    metadata: Optional[Dict] = None

class BulkSensorData(BaseModel):
    readings: List[SensorDataModel]
    tenant_id: str

class SensorAlert(BaseModel):
    asset_id: int
    sensor_id: str
    metric_type: str
    alert_type: str  # threshold, anomaly, trend
    severity: str    # low, medium, high, critical
    message: str
    timestamp: datetime

class TimescaleDBManager:
    def __init__(self):
        self.db_pool = None
        self.alert_thresholds = {
            'temperature': {'warning': 80, 'critical': 100, 'unit': '°C'},
            'vibration': {'warning': 10, 'critical': 15, 'unit': 'mm/s'},
            'pressure': {'warning': 150, 'critical': 200, 'unit': 'PSI'},
            'current': {'warning': 15, 'critical': 20, 'unit': 'A'},
            'humidity': {'warning': 85, 'critical': 95, 'unit': '%'},
            'flow_rate': {'warning': 500, 'critical': 600, 'unit': 'L/min'}
        }
        self.connected_clients = set()
        
    async def initialize(self):
        """Initialize database connection and TimescaleDB setup"""
        try:
            self.db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=3, max_size=15)
            logger.info("✅ Database connection established")
            
            await self.setup_timescaledb_schema()
            await self.create_continuous_aggregates()
            await self.setup_retention_policies()
            
            logger.info("✅ TimescaleDB schema and policies configured")
            
        except Exception as e:
            logger.error(f"❌ TimescaleDB initialization failed: {e}")
            raise

    async def setup_timescaledb_schema(self):
        """Set up TimescaleDB hypertables and indexes"""
        async with self.db_pool.acquire() as conn:
            # Create TimescaleDB extension if not exists
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            
            # Create sensor_data table if not exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    timestamp TIMESTAMPTZ NOT NULL,
                    tenant_id UUID NOT NULL,
                    sensor_id VARCHAR(255) NOT NULL,
                    asset_id INTEGER NOT NULL,
                    metric_type VARCHAR(100) NOT NULL,
                    value NUMERIC(15,4) NOT NULL,
                    unit VARCHAR(50) NOT NULL,
                    quality_score NUMERIC(3,2) DEFAULT 1.0,
                    metadata JSONB DEFAULT '{}'
                );
            """)
            
            # Convert to hypertable if not already
            try:
                await conn.execute("""
                    SELECT create_hypertable('sensor_data', 'timestamp',
                        partitioning_column => 'tenant_id', 
                        number_partitions => 4,
                        if_not_exists => TRUE
                    );
                """)
                logger.info("✅ Hypertable created for sensor_data")
            except Exception as e:
                logger.warning(f"⚠️ Hypertable may already exist: {e}")
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sensor_data_asset_metric ON sensor_data (asset_id, metric_type, timestamp DESC);",
                "CREATE INDEX IF NOT EXISTS idx_sensor_data_sensor ON sensor_data (sensor_id, timestamp DESC);",
                "CREATE INDEX IF NOT EXISTS idx_sensor_data_tenant ON sensor_data (tenant_id, timestamp DESC);",
                "CREATE INDEX IF NOT EXISTS idx_sensor_data_quality ON sensor_data (quality_score) WHERE quality_score < 0.8;"
            ]
            
            for index_sql in indexes:
                try:
                    await conn.execute(index_sql)
                except Exception as e:
                    logger.warning(f"⚠️ Index creation warning: {e}")

    async def create_continuous_aggregates(self):
        """Create continuous aggregates for real-time analytics"""
        async with self.db_pool.acquire() as conn:
            # Hourly aggregates
            await conn.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_data_hourly
                WITH (timescaledb.continuous) AS
                SELECT 
                    time_bucket('1 hour', timestamp) AS hour,
                    tenant_id,
                    asset_id,
                    metric_type,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    STDDEV(value) as stddev_value,
                    COUNT(*) as reading_count,
                    AVG(quality_score) as avg_quality
                FROM sensor_data
                GROUP BY hour, tenant_id, asset_id, metric_type;
            """)
            
            # Daily aggregates
            await conn.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_data_daily
                WITH (timescaledb.continuous) AS
                SELECT 
                    time_bucket('1 day', timestamp) AS day,
                    tenant_id,
                    asset_id,
                    metric_type,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    STDDEV(value) as stddev_value,
                    COUNT(*) as reading_count,
                    AVG(quality_score) as avg_quality
                FROM sensor_data
                GROUP BY day, tenant_id, asset_id, metric_type;
            """)
            
            # Add refresh policies
            try:
                await conn.execute("""
                    SELECT add_continuous_aggregate_policy('sensor_data_hourly',
                        start_offset => INTERVAL '3 hours',
                        end_offset => INTERVAL '1 hour',
                        schedule_interval => INTERVAL '30 minutes',
                        if_not_exists => TRUE);
                """)
                
                await conn.execute("""
                    SELECT add_continuous_aggregate_policy('sensor_data_daily',
                        start_offset => INTERVAL '2 days',
                        end_offset => INTERVAL '1 hour',
                        schedule_interval => INTERVAL '1 hour',
                        if_not_exists => TRUE);
                """)
                
                logger.info("✅ Continuous aggregate policies created")
            except Exception as e:
                logger.warning(f"⚠️ Aggregate policy warning: {e}")

    async def setup_retention_policies(self):
        """Set up data retention policies"""
        async with self.db_pool.acquire() as conn:
            try:
                # Keep raw data for 1 year
                await conn.execute("""
                    SELECT add_retention_policy('sensor_data', INTERVAL '1 year', if_not_exists => TRUE);
                """)
                
                # Keep hourly aggregates for 2 years
                await conn.execute("""
                    SELECT add_retention_policy('sensor_data_hourly', INTERVAL '2 years', if_not_exists => TRUE);
                """)
                
                # Keep daily aggregates for 5 years
                await conn.execute("""
                    SELECT add_retention_policy('sensor_data_daily', INTERVAL '5 years', if_not_exists => TRUE);
                """)
                
                logger.info("✅ Retention policies configured")
            except Exception as e:
                logger.warning(f"⚠️ Retention policy warning: {e}")

    async def ingest_sensor_reading(self, reading: SensorReading) -> bool:
        """Ingest a single sensor reading"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO sensor_data 
                    (timestamp, tenant_id, sensor_id, asset_id, metric_type, value, unit, quality_score, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                reading.timestamp, reading.tenant_id, reading.sensor_id,
                reading.asset_id, reading.metric_type, reading.value,
                reading.unit, reading.quality_score, 
                json.dumps(reading.metadata or {}))
                
                # Check for alerts
                await self.check_for_alerts(reading)
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to ingest sensor reading: {e}")
            return False

    async def ingest_bulk_readings(self, readings: List[SensorReading]) -> Dict:
        """Ingest multiple sensor readings efficiently"""
        try:
            success_count = 0
            error_count = 0
            
            async with self.db_pool.acquire() as conn:
                # Prepare bulk insert
                insert_data = []
                for reading in readings:
                    insert_data.append((
                        reading.timestamp, reading.tenant_id, reading.sensor_id,
                        reading.asset_id, reading.metric_type, reading.value,
                        reading.unit, reading.quality_score,
                        json.dumps(reading.metadata or {})
                    ))
                
                # Execute bulk insert
                await conn.executemany("""
                    INSERT INTO sensor_data 
                    (timestamp, tenant_id, sensor_id, asset_id, metric_type, value, unit, quality_score, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, insert_data)
                
                success_count = len(readings)
                
                # Check for alerts on recent readings
                for reading in readings[-10:]:  # Check last 10 readings for alerts
                    await self.check_for_alerts(reading)
                
            return {
                "success_count": success_count,
                "error_count": error_count,
                "total_processed": len(readings)
            }
            
        except Exception as e:
            logger.error(f"❌ Bulk ingestion failed: {e}")
            return {
                "success_count": 0,
                "error_count": len(readings),
                "total_processed": len(readings),
                "error": str(e)
            }

    async def check_for_alerts(self, reading: SensorReading):
        """Check sensor reading against alert thresholds"""
        try:
            metric_type = reading.metric_type
            value = reading.value
            
            if metric_type in self.alert_thresholds:
                thresholds = self.alert_thresholds[metric_type]
                
                alert_type = None
                severity = None
                
                if value >= thresholds['critical']:
                    alert_type = 'threshold'
                    severity = 'critical'
                elif value >= thresholds['warning']:
                    alert_type = 'threshold'
                    severity = 'high'
                
                if alert_type:
                    alert = SensorAlert(
                        asset_id=reading.asset_id,
                        sensor_id=reading.sensor_id,
                        metric_type=reading.metric_type,
                        alert_type=alert_type,
                        severity=severity,
                        message=f"{metric_type.title()} reading of {value} {reading.unit} exceeds {severity} threshold",
                        timestamp=reading.timestamp
                    )
                    
                    await self.broadcast_alert(alert)
                    
        except Exception as e:
            logger.error(f"❌ Alert check failed: {e}")

    async def broadcast_alert(self, alert: SensorAlert):
        """Broadcast alert to connected WebSocket clients"""
        if self.connected_clients:
            alert_data = {
                "type": "sensor_alert",
                "data": {
                    "asset_id": alert.asset_id,
                    "sensor_id": alert.sensor_id,
                    "metric_type": alert.metric_type,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
            }
            
            message = json.dumps(alert_data)
            
            # Send to all connected clients
            disconnected_clients = set()
            for client in self.connected_clients:
                try:
                    await client.send_text(message)
                except Exception:
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.connected_clients -= disconnected_clients

    async def get_real_time_data(self, asset_id: int, hours_back: int = 1) -> List[Dict]:
        """Get real-time sensor data for an asset"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    timestamp,
                    sensor_id,
                    metric_type,
                    value,
                    unit,
                    quality_score
                FROM sensor_data
                WHERE asset_id = $1
                AND timestamp >= NOW() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
                LIMIT 1000
            """, asset_id, hours_back)
            
            return [dict(row) for row in rows]

    async def get_aggregated_analytics(self, asset_id: int, metric_type: str, 
                                     interval: str = 'hourly', days_back: int = 7) -> List[Dict]:
        """Get aggregated analytics data"""
        table_name = f"sensor_data_{interval}"
        time_column = 'hour' if interval == 'hourly' else 'day'
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT 
                    {time_column} as timestamp,
                    avg_value,
                    min_value,
                    max_value,
                    stddev_value,
                    reading_count,
                    avg_quality
                FROM {table_name}
                WHERE asset_id = $1
                AND metric_type = $2
                AND {time_column} >= NOW() - INTERVAL '%s days'
                ORDER BY {time_column} DESC
            """, asset_id, metric_type, days_back)
            
            return [dict(row) for row in rows]

    async def simulate_iot_data(self, asset_ids: List[int], duration_minutes: int = 60):
        """Simulate IoT sensor data for testing"""
        logger.info(f"🔄 Starting IoT data simulation for {len(asset_ids)} assets")
        
        sensor_types = ['temperature', 'vibration', 'pressure', 'current', 'humidity']
        tenant_id = "00000000-0000-0000-0000-000000000000"  # Default tenant
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            readings = []
            
            for asset_id in asset_ids:
                for sensor_type in sensor_types:
                    # Generate realistic sensor data with some randomness
                    base_values = {
                        'temperature': 65,
                        'vibration': 5,
                        'pressure': 120,
                        'current': 10,
                        'humidity': 45
                    }
                    
                    units = {
                        'temperature': '°C',
                        'vibration': 'mm/s',
                        'pressure': 'PSI',
                        'current': 'A',
                        'humidity': '%'
                    }
                    
                    base_value = base_values[sensor_type]
                    # Add some random variation
                    value = base_value + random.uniform(-base_value*0.1, base_value*0.1)
                    
                    # Occasionally add anomalies for testing
                    if random.random() < 0.05:  # 5% chance of anomaly
                        value *= random.uniform(1.5, 2.0)
                    
                    reading = SensorReading(
                        timestamp=datetime.now(),
                        tenant_id=tenant_id,
                        sensor_id=f"sensor_{asset_id}_{sensor_type}",
                        asset_id=asset_id,
                        metric_type=sensor_type,
                        value=round(value, 2),
                        unit=units[sensor_type],
                        quality_score=random.uniform(0.85, 1.0),
                        metadata={"simulated": True, "location": f"Section_{asset_id % 10}"}
                    )
                    
                    readings.append(reading)
            
            # Bulk insert readings
            result = await self.ingest_bulk_readings(readings)
            logger.info(f"📊 Simulated {result['success_count']} sensor readings")
            
            # Wait before next batch
            await asyncio.sleep(10)  # 10 second intervals
        
        logger.info(f"✅ IoT data simulation completed")

# Initialize TimescaleDB manager
timescale_manager = TimescaleDBManager()

# WebSocket manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        timescale_manager.connected_clients.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        timescale_manager.connected_clients.discard(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize TimescaleDB on startup"""
    await timescale_manager.initialize()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ChatterFix TimescaleDB IoT Integration",
        "timestamp": datetime.now().isoformat(),
        "connected_clients": len(timescale_manager.connected_clients)
    }

@app.post("/api/sensor/ingest")
async def ingest_sensor_data(data: SensorDataModel, tenant_id: str = "default"):
    """Ingest single sensor reading"""
    try:
        reading = SensorReading(
            timestamp=datetime.now(),
            tenant_id=tenant_id,
            sensor_id=data.sensor_id,
            asset_id=data.asset_id,
            metric_type=data.metric_type,
            value=data.value,
            unit=data.unit,
            quality_score=data.quality_score,
            metadata=data.metadata
        )
        
        success = await timescale_manager.ingest_sensor_reading(reading)
        
        if success:
            return {"status": "success", "message": "Sensor data ingested"}
        else:
            raise HTTPException(status_code=500, detail="Failed to ingest sensor data")
            
    except Exception as e:
        logger.error(f"❌ Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sensor/bulk-ingest")
async def bulk_ingest_sensor_data(bulk_data: BulkSensorData):
    """Ingest multiple sensor readings"""
    try:
        readings = []
        for data in bulk_data.readings:
            reading = SensorReading(
                timestamp=datetime.now(),
                tenant_id=bulk_data.tenant_id,
                sensor_id=data.sensor_id,
                asset_id=data.asset_id,
                metric_type=data.metric_type,
                value=data.value,
                unit=data.unit,
                quality_score=data.quality_score,
                metadata=data.metadata
            )
            readings.append(reading)
        
        result = await timescale_manager.ingest_bulk_readings(readings)
        return result
        
    except Exception as e:
        logger.error(f"❌ Bulk ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensor/realtime/{asset_id}")
async def get_realtime_data(asset_id: int, hours_back: int = 1):
    """Get real-time sensor data for an asset"""
    try:
        data = await timescale_manager.get_real_time_data(asset_id, hours_back)
        return {
            "asset_id": asset_id,
            "data": data,
            "count": len(data),
            "hours_back": hours_back
        }
        
    except Exception as e:
        logger.error(f"❌ Real-time data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensor/analytics/{asset_id}/{metric_type}")
async def get_sensor_analytics(asset_id: int, metric_type: str, 
                             interval: str = "hourly", days_back: int = 7):
    """Get aggregated sensor analytics"""
    try:
        if interval not in ['hourly', 'daily']:
            raise HTTPException(status_code=400, detail="Interval must be 'hourly' or 'daily'")
        
        data = await timescale_manager.get_aggregated_analytics(
            asset_id, metric_type, interval, days_back
        )
        
        return {
            "asset_id": asset_id,
            "metric_type": metric_type,
            "interval": interval,
            "data": data,
            "count": len(data)
        }
        
    except Exception as e:
        logger.error(f"❌ Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sensor/simulate")
async def start_simulation(asset_ids: List[int], duration_minutes: int = 60):
    """Start IoT data simulation"""
    try:
        asyncio.create_task(
            timescale_manager.simulate_iot_data(asset_ids, duration_minutes)
        )
        
        return {
            "status": "simulation_started",
            "asset_ids": asset_ids,
            "duration_minutes": duration_minutes,
            "message": f"Simulating IoT data for {len(asset_ids)} assets"
        }
        
    except Exception as e:
        logger.error(f"❌ Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/sensor-alerts")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time sensor alerts"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("📱 WebSocket client disconnected")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8006))
    print(f"📊 Starting ChatterFix TimescaleDB IoT Integration on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)