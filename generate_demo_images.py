#!/usr/bin/env python3
"""
Generate demo image placeholders for ChatterFix CMMS
"""

import os
from PIL import Image, ImageDraw, ImageFont
import random

IMAGES_DIR = "./app/static/images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# Colors for different equipment types
EQUIPMENT_COLORS = {
    "battery_line": "#4CAF50",  # Green
    "gigapress": "#FF5722",  # Deep Orange
    "paint_booth": "#2196F3",  # Blue
    "stamping_press": "#9C27B0",  # Purple
    "air_system": "#607D8B",  # Blue Grey
    "substation": "#FF9800",  # Orange
    "cooling_tower": "#00BCD4",  # Cyan
    "agv_system": "#795548",  # Brown
    "xray_unit": "#E91E63",  # Pink
    "leak_tester": "#8BC34A",  # Light Green
    "crane": "#FFC107",  # Amber
    "forklift": "#3F51B5",  # Indigo
}


def create_equipment_image(name, color, size=(400, 300)):
    """Create a placeholder equipment image"""
    img = Image.new("RGB", size, color=color)
    draw = ImageDraw.Draw(img)

    # Try to use a system font, fallback to default
    try:
        font_large = ImageFont.truetype("Arial.ttf", 24)
        font_small = ImageFont.truetype("Arial.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Add equipment icon (simple rectangle with lines)
    equipment_rect = [50, 50, size[0] - 50, size[1] - 100]
    draw.rectangle(equipment_rect, outline="white", width=3)

    # Add some internal lines to make it look like equipment
    for i in range(3):
        y = 70 + i * 30
        draw.line([70, y, size[0] - 70, y], fill="white", width=2)

    # Add text
    text_lines = name.split()
    y_offset = size[1] - 80
    for line in text_lines[-2:]:  # Show last 2 words
        bbox = draw.textbbox((0, 0), line, font=font_small)
        text_width = bbox[2] - bbox[0]
        x = (size[0] - text_width) // 2
        draw.text((x, y_offset), line, fill="white", font=font_small)
        y_offset += 20

    return img


def create_part_image(name, color, size=(200, 150)):
    """Create a placeholder part image"""
    img = Image.new("RGB", size, color=color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("Arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    # Add part icon (circle with details)
    center_x, center_y = size[0] // 2, size[1] // 2
    radius = min(size[0], size[1]) // 3
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        outline="white",
        width=2,
    )

    # Add some detail lines
    draw.line(
        [center_x - radius // 2, center_y, center_x + radius // 2, center_y],
        fill="white",
        width=2,
    )
    draw.line(
        [center_x, center_y - radius // 2, center_x, center_y + radius // 2],
        fill="white",
        width=2,
    )

    # Add text
    words = name.split()[:2]  # First 2 words
    y_offset = size[1] - 30
    for word in words:
        bbox = draw.textbbox((0, 0), word, font=font)
        text_width = bbox[2] - bbox[0]
        x = (size[0] - text_width) // 2
        draw.text((x, y_offset), word, fill="white", font=font)
        y_offset += 15

    return img


def generate_demo_images():
    """Generate all demo images"""

    # Equipment images
    equipment_images = [
        ("battery_line.jpg", "Battery Assembly Line", EQUIPMENT_COLORS["battery_line"]),
        ("gigapress.jpg", "Gigapress Machine", EQUIPMENT_COLORS["gigapress"]),
        ("paint_booth.jpg", "Paint Booth Station", EQUIPMENT_COLORS["paint_booth"]),
        ("stamping_press.jpg", "Stamping Press", EQUIPMENT_COLORS["stamping_press"]),
        ("air_system.jpg", "Air Compressor System", EQUIPMENT_COLORS["air_system"]),
        ("substation.jpg", "Electrical Substation", EQUIPMENT_COLORS["substation"]),
        ("cooling_tower.jpg", "Cooling Tower", EQUIPMENT_COLORS["cooling_tower"]),
        ("agv_system.jpg", "AGV Fleet Controller", EQUIPMENT_COLORS["agv_system"]),
        ("xray_unit.jpg", "X-Ray Inspection", EQUIPMENT_COLORS["xray_unit"]),
        ("leak_tester.jpg", "Leak Test Station", EQUIPMENT_COLORS["leak_tester"]),
        ("crane.jpg", "Mobile Crane", EQUIPMENT_COLORS["crane"]),
        ("forklift.jpg", "Electric Forklift", EQUIPMENT_COLORS["forklift"]),
    ]

    for filename, name, color in equipment_images:
        img = create_equipment_image(name, color)
        img.save(os.path.join(IMAGES_DIR, filename))
        print(f"✅ Created {filename}")

    # Part images
    part_colors = ["#546E7A", "#8D6E63", "#7CB342", "#FB8C00", "#8E24AA", "#5E35B1"]
    part_images = [
        ("battery_cell.jpg", "Battery Cell"),
        ("battery_housing.jpg", "Battery Housing"),
        ("cooling_plate.jpg", "Cooling Plate"),
        ("hydraulic_seal.jpg", "Hydraulic Seal"),
        ("die_insert.jpg", "Die Insert"),
        ("lube_pump.jpg", "Lube Pump"),
        ("paint_nozzle.jpg", "Paint Nozzle"),
        ("color_valve.jpg", "Color Valve"),
        ("overspray_filter.jpg", "Overspray Filter"),
        ("bearing.jpg", "Industrial Bearing"),
        ("vbelt.jpg", "V-Belt"),
        ("hydraulic_fluid.jpg", "Hydraulic Fluid"),
        ("safety_relay.jpg", "Safety Relay"),
        ("pneumatic_cylinder.jpg", "Pneumatic Cylinder"),
    ]

    for i, (filename, name) in enumerate(part_images):
        color = part_colors[i % len(part_colors)]
        img = create_part_image(name, color)
        img.save(os.path.join(IMAGES_DIR, filename))
        print(f"✅ Created {filename}")

    # User avatar images
    avatar_colors = [
        "#FF5722",
        "#4CAF50",
        "#2196F3",
        "#FF9800",
        "#9C27B0",
        "#607D8B",
        "#E91E63",
    ]
    avatars = [
        "admin.jpg",
        "sarah.jpg",
        "mike.jpg",
        "alex.jpg",
        "jennifer.jpg",
        "david.jpg",
        "lisa.jpg",
    ]

    for i, avatar in enumerate(avatars):
        img = Image.new("RGB", (100, 100), color=avatar_colors[i])
        draw = ImageDraw.Draw(img)

        # Draw simple avatar circle
        draw.ellipse([20, 20, 80, 80], fill="white")
        draw.ellipse([30, 30, 70, 70], fill=avatar_colors[i])

        # Add initials
        initials = avatar.replace(".jpg", "").upper()[:2]
        try:
            font = ImageFont.truetype("Arial.ttf", 16)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (100 - text_width) // 2
        y = (100 - text_height) // 2
        draw.text((x, y), initials, fill="white", font=font)

        img.save(os.path.join(IMAGES_DIR, avatar))
        print(f"✅ Created {avatar}")

    print(
        f"\n🎉 Generated {len(equipment_images) + len(part_images) + len(avatars)} demo images!"
    )


if __name__ == "__main__":
    generate_demo_images()
