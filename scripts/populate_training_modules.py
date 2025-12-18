#!/usr/bin/env python3
"""
Populate Training Modules Database
Creates sample training modules for ChatterFix CMMS
"""

import json
import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the path so we can import modules
sys.path.append('/Users/fredtaylor/ChatterFix')

from app.core.firestore_db import get_firestore_manager

# Sample training modules
SAMPLE_TRAINING_MODULES = [
    {
        "id": "1",
        "title": "Hydraulic Pump Maintenance",
        "description": "Comprehensive training on hydraulic pump operation, maintenance, and troubleshooting",
        "content_type": "standard",
        "asset_type": "Hydraulic Pump",
        "skill_category": "Hydraulics",
        "difficulty_level": 3,
        "estimated_duration_minutes": 45,
        "content_path": json.dumps({
            "sections": [
                {
                    "title": "Safety Procedures",
                    "content": "Always ensure system is depressurized before maintenance. Wear safety glasses and gloves. Follow lockout/tagout procedures."
                },
                {
                    "title": "Operating Procedures",
                    "content": "1. Check fluid levels\n2. Inspect for leaks\n3. Verify pressure settings\n4. Test emergency shutoff"
                },
                {
                    "title": "Maintenance Tasks",
                    "content": "• Daily: Visual inspection\n• Weekly: Check fluid levels\n• Monthly: Filter replacement\n• Quarterly: Pressure testing"
                },
                {
                    "title": "Troubleshooting Guide",
                    "content": "Low pressure: Check fluid level and filters\nNoise: Inspect for air in system\nOverheating: Check cooling system"
                }
            ],
            "quiz": [
                {
                    "question": "What should you check first when hydraulic pressure is low?",
                    "options": ["Pump motor", "Fluid level", "Temperature", "Valve settings"],
                    "correct_answer": 1,
                    "explanation": "Low fluid level is the most common cause of low hydraulic pressure"
                }
            ]
        }),
        "ai_generated": False
    },
    {
        "id": "2", 
        "title": "Conveyor Belt System Basics",
        "description": "Introduction to conveyor belt operation, safety, and routine maintenance",
        "content_type": "standard",
        "asset_type": "Conveyor Belt",
        "skill_category": "Mechanical",
        "difficulty_level": 2,
        "estimated_duration_minutes": 30,
        "content_path": json.dumps({
            "sections": [
                {
                    "title": "Safety First",
                    "content": "Never attempt maintenance while conveyor is running. Use proper lockout procedures. Ensure all personnel are clear before startup."
                },
                {
                    "title": "Belt Inspection",
                    "content": "Check for cracks, cuts, and worn edges. Measure belt tension. Inspect splice joints."
                },
                {
                    "title": "Lubrication Points",
                    "content": "Bearing lubrication every 500 hours. Drive motor grease points monthly. Chain drives require weekly lubrication."
                }
            ],
            "quiz": [
                {
                    "question": "How often should conveyor bearings be lubricated?",
                    "options": ["Daily", "Weekly", "Every 500 hours", "Monthly"],
                    "correct_answer": 2,
                    "explanation": "Bearings should be lubricated every 500 operating hours to prevent premature failure"
                }
            ]
        }),
        "ai_generated": False
    },
    {
        "id": "3",
        "title": "Electrical Safety and Basic Troubleshooting", 
        "description": "Fundamental electrical safety procedures and basic troubleshooting techniques",
        "content_type": "standard",
        "asset_type": "Electrical System",
        "skill_category": "Electrical",
        "difficulty_level": 4,
        "estimated_duration_minutes": 60,
        "content_path": json.dumps({
            "sections": [
                {
                    "title": "Electrical Safety",
                    "content": "CRITICAL: Always use lockout/tagout procedures. Test circuits with multimeter before touching. Wear appropriate PPE including insulated gloves."
                },
                {
                    "title": "Basic Measurements",
                    "content": "Voltage testing: Set multimeter to AC voltage, black lead to neutral/ground, red to hot wire.\nCurrent testing: Use clamp meter around single conductor.\nResistance testing: Only on de-energized circuits."
                },
                {
                    "title": "Common Issues",
                    "content": "Blown fuses: Check for shorts before replacing\nTripped breakers: Determine root cause\nLoose connections: Use thermal imaging to identify"
                }
            ],
            "quiz": [
                {
                    "question": "Before testing resistance, you must:",
                    "options": ["Turn on the power", "De-energize the circuit", "Use a clamp meter", "Check voltage first"],
                    "correct_answer": 1,
                    "explanation": "Resistance can only be accurately measured on de-energized circuits to prevent damage to the meter and ensure safety"
                }
            ]
        }),
        "ai_generated": False
    }
]

async def populate_training_modules():
    """Populate the database with sample training modules"""
    print("🚀 Starting training module population...")
    
    try:
        firestore_manager = get_firestore_manager()
        
        # Check if modules already exist
        existing_modules = await firestore_manager.get_collection("training_modules")
        print(f"📊 Found {len(existing_modules)} existing training modules")
        
        # Create modules with specific IDs
        created_count = 0
        for module_data in SAMPLE_TRAINING_MODULES:
            module_id = module_data.pop("id")  # Remove ID from data
            
            try:
                # Check if this specific ID already exists
                existing = await firestore_manager.get_document("training_modules", module_id)
                
                if existing:
                    print(f"⏸️  Module {module_id} already exists: {existing.get('title')}")
                    continue
                
                # Create the module with the specific ID
                created_id = await firestore_manager.create_document(
                    "training_modules", 
                    module_data, 
                    doc_id=module_id
                )
                print(f"✅ Created module {created_id}: {module_data['title']}")
                created_count += 1
                
            except Exception as e:
                print(f"❌ Error creating module {module_id}: {e}")
                continue
        
        print(f"🎉 Successfully created {created_count} training modules")
        
        # Verify the modules exist
        print("\n🔍 Verifying created modules...")
        for i in range(1, 4):
            module = await firestore_manager.get_document("training_modules", str(i))
            if module:
                print(f"✅ Module {i}: {module.get('title')}")
            else:
                print(f"❌ Module {i}: Not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during population: {e}")
        return False

async def main():
    """Main function"""
    print("📚 ChatterFix Training Module Population")
    print("=" * 50)
    
    success = await populate_training_modules()
    
    if success:
        print("\n✅ Training module population completed successfully!")
        print("\n🌐 Test URLs:")
        print("   https://chatterfix.com/training/modules/1")
        print("   https://chatterfix.com/training/modules/2") 
        print("   https://chatterfix.com/training/modules/3")
    else:
        print("\n❌ Training module population failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)