"""
Geolocation Service - Property Boundary Tracking
Manages user location tracking with property boundary restrictions and privacy controls
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.core.database import get_db_connection


class GeolocationService:
    """Service for managing user location tracking with property boundaries"""

    def __init__(self):
        self.conn = None

    def check_location_permission(self, user_id: int) -> bool:
        """Check if user has location tracking enabled"""
        conn = get_db_connection()
        cur = conn.cursor()

        settings = cur.execute(
            """
            SELECT location_tracking_enabled, track_only_on_shift
            FROM user_privacy_settings
            WHERE user_id = ?
        """,
            (user_id,),
        ).fetchone()

        conn.close()

        if not settings:
            # Default to enabled if no settings exist
            return True

        return settings["location_tracking_enabled"]

    def update_user_location(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        accuracy: float = None,
        work_order_id: int = None,
    ) -> Dict:
        """Update user's current location and check if within property boundaries"""

        # Check permission first
        if not self.check_location_permission(user_id):
            return {"success": False, "error": "Location tracking disabled by user"}

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if location is within any active property boundary
        within_property = self.is_within_property(latitude, longitude)

        # Update user's current location
        cur.execute(
            """
            UPDATE users
            SET current_latitude = ?, current_longitude = ?, last_location_update = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (latitude, longitude, user_id),
        )

        # Log location history
        cur.execute(
            """
            INSERT INTO user_location_history
            (user_id, latitude, longitude, accuracy, work_order_id, within_property)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (user_id, latitude, longitude, accuracy, work_order_id, within_property),
        )

        conn.commit()
        conn.close()

        return {
            "success": True,
            "within_property": within_property,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": datetime.now().isoformat(),
        }

    def is_within_property(self, latitude: float, longitude: float) -> bool:
        """Check if coordinates are within any active property boundary"""
        conn = get_db_connection()
        cur = conn.cursor()

        boundaries = cur.execute(
            """
            SELECT id, coordinates, boundary_type
            FROM property_boundaries
            WHERE is_active = 1
        """
        ).fetchall()

        conn.close()

        for boundary in boundaries:
            coords = json.loads(boundary["coordinates"])

            if boundary["boundary_type"] == "polygon":
                if self._point_in_polygon(latitude, longitude, coords):
                    return True
            elif boundary["boundary_type"] == "circle":
                if self._point_in_circle(latitude, longitude, coords):
                    return True

        return False

    def _point_in_polygon(
        self, lat: float, lon: float, polygon: List[List[float]]
    ) -> bool:
        """Check if point is inside polygon using ray casting algorithm"""
        x, y = lat, lon
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def _point_in_circle(self, lat: float, lon: float, circle: Dict) -> bool:
        """Check if point is inside circle (radius in meters)"""
        center_lat = circle["center"][0]
        center_lon = circle["center"][1]
        radius = circle["radius"]

        # Haversine formula for distance
        from math import radians, cos, sin, asin, sqrt

        lon1, lat1, lon2, lat2 = map(radians, [lon, lat, center_lon, center_lat])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Radius of earth in meters

        distance = c * r
        return distance <= radius

    def get_user_location(self, user_id: int) -> Optional[Dict]:
        """Get user's current location"""
        conn = get_db_connection()
        cur = conn.cursor()

        location = cur.execute(
            """
            SELECT current_latitude, current_longitude, last_location_update
            FROM users
            WHERE id = ?
        """,
            (user_id,),
        ).fetchone()

        conn.close()

        if location and location["current_latitude"]:
            return {
                "latitude": location["current_latitude"],
                "longitude": location["current_longitude"],
                "last_update": location["last_location_update"],
            }

        return None

    def get_team_locations(self, user_id: int) -> List[Dict]:
        """Get locations of team members who have sharing enabled"""
        conn = get_db_connection()
        cur = conn.cursor()

        locations = cur.execute(
            """
            SELECT
                u.id,
                u.full_name,
                u.username,
                u.role,
                u.current_latitude,
                u.current_longitude,
                u.last_location_update,
                u.status
            FROM users u
            LEFT JOIN user_privacy_settings ups ON u.id = ups.user_id
            WHERE u.id != ?
            AND u.current_latitude IS NOT NULL
            AND (ups.share_location_with_team = 1 OR ups.share_location_with_team IS NULL)
            AND datetime(u.last_location_update) > datetime('now', '-1 hour')
        """,
            (user_id,),
        ).fetchall()

        conn.close()

        return [dict(loc) for loc in locations]

    def get_nearby_work_orders(
        self, user_id: int, radius_meters: int = 500
    ) -> List[Dict]:
        """Get work orders near user's current location"""
        user_location = self.get_user_location(user_id)

        if not user_location:
            return []

        conn = get_db_connection()
        cur = conn.cursor()

        # Get work orders with location data
        work_orders = cur.execute(
            """
            SELECT
                wo.id,
                wo.title,
                wo.priority,
                wo.status,
                wo.location,
                a.name as asset_name
            FROM work_orders wo
            LEFT JOIN assets a ON wo.asset_id = a.id
            WHERE wo.status NOT IN ('completed', 'cancelled')
            AND wo.location IS NOT NULL
        """
        ).fetchall()

        conn.close()

        # Filter by distance (simplified - would need actual coordinates)
        # This is a placeholder for demonstration
        nearby = []
        for wo in work_orders:
            # In production, parse location and calculate distance
            nearby.append(dict(wo))

        return nearby

    def update_privacy_settings(self, user_id: int, settings: Dict) -> bool:
        """Update user's location privacy settings"""
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                INSERT OR REPLACE INTO user_privacy_settings
                (user_id, location_tracking_enabled, share_location_with_team, track_only_on_shift, updated_date)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    user_id,
                    settings.get("location_tracking_enabled", 1),
                    settings.get("share_location_with_team", 1),
                    settings.get("track_only_on_shift", 1),
                ),
            )
            conn.commit()
            success = True
        except Exception as e:
            print(f"Error updating privacy settings: {e}")
            success = False
        finally:
            conn.close()

        return success

    def get_privacy_settings(self, user_id: int) -> Dict:
        """Get user's location privacy settings"""
        conn = get_db_connection()
        cur = conn.cursor()

        settings = cur.execute(
            """
            SELECT
                location_tracking_enabled,
                share_location_with_team,
                track_only_on_shift
            FROM user_privacy_settings
            WHERE user_id = ?
        """,
            (user_id,),
        ).fetchone()

        conn.close()

        if settings:
            return dict(settings)

        # Return defaults if no settings exist
        return {
            "location_tracking_enabled": True,
            "share_location_with_team": True,
            "track_only_on_shift": True,
        }

    def add_property_boundary(
        self,
        name: str,
        coordinates: List,
        boundary_type: str = "polygon",
        description: str = None,
    ) -> int:
        """Add a new property boundary"""
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO property_boundaries (name, description, boundary_type, coordinates)
            VALUES (?, ?, ?, ?)
        """,
            (name, description, boundary_type, json.dumps(coordinates)),
        )

        boundary_id = cur.lastrowid
        conn.commit()
        conn.close()

        return boundary_id

    def get_location_history(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get user's location history"""
        conn = get_db_connection()
        cur = conn.cursor()

        history = cur.execute(
            """
            SELECT
                latitude,
                longitude,
                accuracy,
                work_order_id,
                within_property,
                timestamp
            FROM user_location_history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (user_id, limit),
        ).fetchall()

        conn.close()

        return [dict(h) for h in history]


# Global instance
geolocation_service = GeolocationService()
