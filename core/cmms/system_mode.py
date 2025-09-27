#!/usr/bin/env python3
"""
System Mode Utility Module
Provides system-wide access to demo/production mode settings
"""


def get_system_mode():
    """Get current system mode from admin config"""
    try:
        from admin import get_system_mode as admin_get_mode

        return admin_get_mode()
    except ImportError:
        # Fallback to production mode if admin module not available
        return "production"


def is_demo_mode():
    """Check if system is in demo mode"""
    return get_system_mode() == "demo"


def is_production_mode():
    """Check if system is in production mode"""
    return get_system_mode() == "production"


def get_demo_features():
    """Get demo features configuration"""
    try:
        from admin import get_demo_features as admin_get_features

        return admin_get_features()
    except ImportError:
        # Fallback demo features
        return {
            "show_sample_data": True,
            "limited_functionality": True,
            "demo_watermark": True,
            "auto_reset_data": True,
        }


def demo_mode_decorator(func):
    """Decorator to modify behavior in demo mode"""

    def wrapper(*args, **kwargs):
        if is_demo_mode():
            features = get_demo_features()
            # Add demo context to kwargs
            kwargs["demo_mode"] = True
            kwargs["demo_features"] = features
        else:
            kwargs["demo_mode"] = False
            kwargs["demo_features"] = None
        return func(*args, **kwargs)

    return wrapper


def production_only(func):
    """Decorator to restrict functions to production mode only"""

    def wrapper(*args, **kwargs):
        if is_demo_mode():
            return {
                "error": "Function not available in demo mode",
                "mode": "demo",
                "message": "This feature is restricted in demo mode for safety",
            }
        return func(*args, **kwargs)

    return wrapper


# Example usage for other modules:
"""
from system_mode import is_demo_mode, is_production_mode, demo_mode_decorator

@demo_mode_decorator
def create_work_order(title, **kwargs):
    if kwargs.get('demo_mode'):
        # Demo behavior - perhaps limit functionality or add watermarks
        print("🧪 Creating demo work order...")
        return {"id": "DEMO-001", "title": title, "demo": True}
    else:
        # Production behavior
        print("🚀 Creating production work order...")
        return {"id": "WO-001", "title": title, "demo": False}

# Or simple checks:
if is_demo_mode():
    # Show demo data
    pass
else:
    # Show production data
    pass
"""
