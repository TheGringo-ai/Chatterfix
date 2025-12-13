"""
ChatterFix IoT Advanced Module
Premium sensor integration and predictive analytics platform
"""

from .licensing import require_iot_license, check_iot_access
from .sensor_manager import SensorManager
from .analytics_engine import PredictiveAnalytics
from .dashboard import IoTDashboard

__version__ = "1.0.0"
__all__ = ["require_iot_license", "check_iot_access", "SensorManager", "PredictiveAnalytics", "IoTDashboard"]