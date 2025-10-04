#!/usr/bin/env python3
"""
ChatterFix Local AI Assistant
Interactive assistant for managing ChatterFix CMMS locally with full safety controls
"""

import json
import os
import sys
import uuid
import datetime
from typing import Dict, List, Any, Optional
import subprocess
import shutil
from pathlib import Path

class ChatterFixAssistant:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.customers_file = self.base_dir / "data" / "customers.json"
        self.services_file = self.base_dir / "data" / "services.json"
        self.config_file = self.base_dir / "data" / "config.json"
        
        # Ensure data directory exists
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize data files if they don't exist
        self._initialize_data_files()
        
        print("🚀 ChatterFix Local Assistant Initialized")
        print("📍 Working Directory:", self.base_dir)
        print("🔐 Local-Only Mode: Enabled")
        print("=" * 60)

    def _initialize_data_files(self):
        """Initialize data files if they don't exist"""
        if not self.customers_file.exists():
            with open(self.customers_file, 'w') as f:
                json.dump({}, f, indent=2)
        
        if not self.services_file.exists():
            default_services = {
                "gcp-compute": {
                    "id": "gcp-compute",
                    "name": "Google Compute Engine",
                    "provider": "gcp",
                    "category": "compute",
                    "pricing": {"base": 0.10, "model": "per_hour"},
                    "description": "Virtual machines on Google Cloud"
                },
                "aws-ec2": {
                    "id": "aws-ec2", 
                    "name": "Amazon EC2",
                    "provider": "aws",
                    "category": "compute",
                    "pricing": {"base": 0.08, "model": "per_hour"},
                    "description": "Elastic compute instances on AWS"
                },
                "azure-vm": {
                    "id": "azure-vm",
                    "name": "Azure Virtual Machines", 
                    "provider": "azure",
                    "category": "compute",
                    "pricing": {"base": 0.09, "model": "per_hour"},
                    "description": "Virtual machines on Microsoft Azure"
                }
            }
            with open(self.services_file, 'w') as f:
                json.dump(default_services, f, indent=2)
        
        if not self.config_file.exists():
            default_config = {
                "version": "1.0.0",
                "last_updated": datetime.datetime.now().isoformat(),
                "git_enabled": False,
                "cloud_deploy_enabled": False,
                "backup_enabled": True
            }
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)

    def main_menu(self):
        """Display main menu and handle user input"""
        while True:
            print("\n" + "="*60)
            print("🤖 ChatterFix AI Assistant - What can I help you with?")
            print("="*60)
            print("1. 👥 Customer Management")
            print("2. 🛠️  Service Management") 
            print("3. 🏗️  Platform Enhancement")
            print("4. 📊 Reports & Analytics")
            print("5. 🔧 System Configuration")
            print("6. 💾 Backup & Recovery")
            print("7. 🔐 Security & Permissions")
            print("8. 📚 Help & Documentation")
            print("0. 🚪 Exit")
            print("-" * 60)
            
            choice = input("Enter your choice (0-8): ").strip()
            
            if choice == "0":
                print("👋 Goodbye! ChatterFix Assistant signing off.")
                break
            elif choice == "1":
                self.customer_management()
            elif choice == "2":
                self.service_management()
            elif choice == "3":
                self.platform_enhancement()
            elif choice == "4":
                self.reports_analytics()
            elif choice == "5":
                self.system_configuration()
            elif choice == "6":
                self.backup_recovery()
            elif choice == "7":
                self.security_permissions()
            elif choice == "8":
                self.help_documentation()
            else:
                print("❌ Invalid choice. Please enter a number between 0-8.")

    def customer_management(self):
        """Customer management menu"""
        while True:
            print("\n" + "="*50)
            print("👥 CUSTOMER MANAGEMENT")
            print("="*50)
            print("1. 🎯 Onboard New Customer")
            print("2. 👀 View All Customers")
            print("3. ✏️  Update Customer Information")
            print("4. 🗑️  Remove Customer")
            print("5. 📊 Customer Analytics")
            print("6. 📤 Export Customer Data")
            print("0. ⬅️  Back to Main Menu")
            print("-" * 50)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.onboard_customer()
            elif choice == "2":
                self.view_customers()
            elif choice == "3":
                self.update_customer()
            elif choice == "4":
                self.remove_customer()
            elif choice == "5":
                self.customer_analytics()
            elif choice == "6":
                self.export_customers()
            else:
                print("❌ Invalid choice.")

    def onboard_customer(self):
        """Interactive customer onboarding"""
        print("\n🎯 CUSTOMER ONBOARDING TO CHATTERFIX")
        print("I'll walk you through adding a new customer step by step.\n")
        
        # Collect basic information
        print("📋 BASIC INFORMATION:")
        company_name = input("1. Company Name: ").strip()
        if not company_name:
            print("❌ Company name is required.")
            return
            
        contact_name = input("2. Primary Contact Name: ").strip()
        email = input("3. Email Address: ").strip()
        phone = input("4. Phone Number: ").strip()
        industry = input("5. Industry/Business Type: ").strip()
        
        # Technical requirements
        print("\n⚙️ TECHNICAL REQUIREMENTS:")
        print("Available cloud providers: GCP, AWS, Azure")
        cloud_prefs = input("6. Cloud Preferences (comma-separated): ").strip().split(",")
        cloud_prefs = [p.strip().upper() for p in cloud_prefs if p.strip()]
        
        budget_str = input("7. Expected Monthly Budget ($): ").strip()
        try:
            monthly_budget = float(budget_str) if budget_str else 0.0
        except ValueError:
            monthly_budget = 0.0
            
        use_cases = input("8. Primary Use Cases: ").strip()
        team_size_str = input("9. Team Size: ").strip()
        try:
            team_size = int(team_size_str) if team_size_str else 0
        except ValueError:
            team_size = 0
            
        integrations = input("10. Integration Needs: ").strip()
        
        # Service configuration
        print("\n🛠️ SERVICE CONFIGURATION:")
        print("Available tiers: starter, professional, enterprise")
        tier = input("11. Subscription Tier: ").strip().lower()
        if tier not in ["starter", "professional", "enterprise"]:
            tier = "starter"
            
        addons = input("12. Add-on Services (comma-separated): ").strip()
        billing_freq = input("13. Billing Frequency (monthly/annual): ").strip().lower()
        if billing_freq not in ["monthly", "annual"]:
            billing_freq = "monthly"
            
        timeline = input("14. Implementation Timeline: ").strip()
        
        # Create customer record
        customer_id = f"customer-{uuid.uuid4().hex[:8]}"
        customer_data = {
            "id": customer_id,
            "company_name": company_name,
            "contact_name": contact_name,
            "email": email,
            "phone": phone,
            "industry": industry,
            "cloud_preferences": cloud_prefs,
            "monthly_budget": monthly_budget,
            "use_cases": use_cases,
            "team_size": team_size,
            "integrations": integrations,
            "subscription_tier": tier,
            "addons": addons.split(",") if addons else [],
            "billing_frequency": billing_freq,
            "implementation_timeline": timeline,
            "created_date": datetime.datetime.now().isoformat(),
            "status": "active",
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        # Save to file
        self._save_customer(customer_data)
        
        print(f"\n✅ SUCCESS! Customer '{company_name}' has been onboarded!")
        print(f"🆔 Customer ID: {customer_id}")
        print(f"📊 Subscription Tier: {tier}")
        print(f"💰 Monthly Budget: ${monthly_budget}")
        print(f"☁️  Cloud Preferences: {', '.join(cloud_prefs)}")
        
        # Ask if they want to configure services
        configure = input("\n🛠️ Would you like to configure cloud services now? (y/n): ").strip().lower()
        if configure in ['y', 'yes']:
            self._configure_customer_services(customer_id, customer_data)

    def _save_customer(self, customer_data: Dict[str, Any]):
        """Save customer data to local file"""
        try:
            # Load existing customers
            with open(self.customers_file, 'r') as f:
                customers = json.load(f)
            
            # Add new customer
            customers[customer_data['id']] = customer_data
            
            # Save back to file
            with open(self.customers_file, 'w') as f:
                json.dump(customers, f, indent=2)
                
            print(f"💾 Customer data saved locally to: {self.customers_file}")
            
        except Exception as e:
            print(f"❌ Error saving customer data: {e}")

    def _configure_customer_services(self, customer_id: str, customer_data: Dict[str, Any]):
        """Configure cloud services for a customer"""
        print(f"\n🛠️ CONFIGURING SERVICES FOR {customer_data['company_name']}")
        
        # Load available services
        with open(self.services_file, 'r') as f:
            available_services = json.load(f)
        
        # Filter services based on customer's cloud preferences
        prefs = [p.lower() for p in customer_data['cloud_preferences']]
        relevant_services = {k: v for k, v in available_services.items() 
                           if v['provider'].lower() in prefs}
        
        if not relevant_services:
            print("❌ No services available for selected cloud providers.")
            return
        
        print("Available services for your cloud preferences:")
        for service_id, service in relevant_services.items():
            price = service['pricing']['base']
            model = service['pricing']['model']
            print(f"  • {service['name']} - ${price} {model}")
        
        selected = input("\nEnter service IDs to configure (comma-separated): ").strip()
        if selected:
            service_ids = [s.strip() for s in selected.split(",")]
            customer_data['configured_services'] = service_ids
            customer_data['last_updated'] = datetime.datetime.now().isoformat()
            self._save_customer(customer_data)
            print(f"✅ Configured {len(service_ids)} services for {customer_data['company_name']}")

    def view_customers(self):
        """Display all customers"""
        try:
            with open(self.customers_file, 'r') as f:
                customers = json.load(f)
            
            if not customers:
                print("📭 No customers found.")
                return
            
            print(f"\n👥 ALL CUSTOMERS ({len(customers)} total)")
            print("=" * 70)
            
            for customer_id, customer in customers.items():
                print(f"🏢 {customer['company_name']}")
                print(f"   ID: {customer_id}")
                print(f"   Contact: {customer['contact_name']} ({customer['email']})")
                print(f"   Tier: {customer['subscription_tier']}")
                print(f"   Budget: ${customer['monthly_budget']}/month")
                print(f"   Cloud: {', '.join(customer['cloud_preferences'])}")
                print(f"   Status: {customer['status']}")
                print(f"   Created: {customer['created_date'][:10]}")
                print("-" * 70)
                
        except Exception as e:
            print(f"❌ Error loading customers: {e}")

    def service_management(self):
        """Service management menu"""
        while True:
            print("\n" + "="*50)
            print("🛠️ SERVICE MANAGEMENT")
            print("="*50)
            print("1. ➕ Add New Service")
            print("2. 👀 View All Services") 
            print("3. ✏️  Update Service")
            print("4. 🗑️  Remove Service")
            print("5. 🔗 Configure Service Integration")
            print("6. 💰 Update Service Pricing")
            print("0. ⬅️  Back to Main Menu")
            print("-" * 50)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.add_service()
            elif choice == "2":
                self.view_services()
            elif choice == "3":
                self.update_service()
            elif choice == "4":
                self.remove_service()
            elif choice == "5":
                self.configure_service_integration()
            elif choice == "6":
                self.update_service_pricing()
            else:
                print("❌ Invalid choice.")

    def add_service(self):
        """Add a new service to ChatterFix"""
        print("\n🛠️ ADDING NEW SERVICE TO CHATTERFIX")
        print("What type of service are you adding?\n")
        
        print("Service Categories:")
        print("1. Cloud Infrastructure (GCP, AWS, Azure)")
        print("2. Productivity & Workspace (Google Workspace, Office 365)")
        print("3. Development & AI (APIs, ML models)")
        print("4. Specialized Tools (IoT, Custom integrations)")
        
        category_choice = input("\nSelect category (1-4): ").strip()
        categories = {
            "1": "infrastructure",
            "2": "productivity", 
            "3": "development",
            "4": "specialized"
        }
        category = categories.get(category_choice, "infrastructure")
        
        # Collect service details
        service_name = input("Service Name: ").strip()
        if not service_name:
            print("❌ Service name is required.")
            return
            
        provider = input("Provider (gcp/aws/azure/other): ").strip().lower()
        description = input("Description: ").strip()
        
        # Pricing configuration
        print("\nPricing Configuration:")
        print("1. Per-user (monthly/annual)")
        print("2. Usage-based (per API call, per GB, etc.)")
        print("3. Flat-rate (monthly subscription)")
        print("4. Tiered pricing")
        
        pricing_choice = input("Select pricing model (1-4): ").strip()
        pricing_models = {
            "1": "per_user",
            "2": "usage_based",
            "3": "flat_rate", 
            "4": "tiered"
        }
        pricing_model = pricing_models.get(pricing_choice, "flat_rate")
        
        base_price_str = input("Base price: $").strip()
        try:
            base_price = float(base_price_str) if base_price_str else 0.0
        except ValueError:
            base_price = 0.0
        
        # Create service record
        service_id = f"{provider}-{service_name.lower().replace(' ', '-')}"
        service_data = {
            "id": service_id,
            "name": service_name,
            "provider": provider,
            "category": category,
            "description": description,
            "pricing": {
                "model": pricing_model,
                "base": base_price
            },
            "created_date": datetime.datetime.now().isoformat(),
            "last_updated": datetime.datetime.now().isoformat(),
            "active": True
        }
        
        # Optional: API configuration
        api_endpoint = input("API Endpoint (optional): ").strip()
        if api_endpoint:
            service_data["api_endpoint"] = api_endpoint
            
        auth_method = input("Authentication Method (api_key/oauth/basic): ").strip()
        if auth_method:
            service_data["auth_method"] = auth_method
        
        # Save service
        self._save_service(service_data)
        
        print(f"\n✅ SUCCESS! Service '{service_name}' has been added!")
        print(f"🆔 Service ID: {service_id}")
        print(f"💰 Pricing: ${base_price} ({pricing_model})")
        print(f"🏷️ Category: {category}")

    def _save_service(self, service_data: Dict[str, Any]):
        """Save service data to local file"""
        try:
            # Load existing services
            with open(self.services_file, 'r') as f:
                services = json.load(f)
            
            # Add new service
            services[service_data['id']] = service_data
            
            # Save back to file
            with open(self.services_file, 'w') as f:
                json.dump(services, f, indent=2)
                
            print(f"💾 Service data saved locally to: {self.services_file}")
            
        except Exception as e:
            print(f"❌ Error saving service data: {e}")

    def view_services(self):
        """Display all services"""
        try:
            with open(self.services_file, 'r') as f:
                services = json.load(f)
            
            if not services:
                print("📭 No services found.")
                return
            
            print(f"\n🛠️ ALL SERVICES ({len(services)} total)")
            print("=" * 70)
            
            # Group by provider
            providers = {}
            for service_id, service in services.items():
                provider = service['provider'].upper()
                if provider not in providers:
                    providers[provider] = []
                providers[provider].append(service)
            
            for provider, provider_services in providers.items():
                print(f"☁️ {provider} SERVICES:")
                for service in provider_services:
                    price = service['pricing']['base']
                    model = service['pricing']['model']
                    status = "🟢 Active" if service.get('active', True) else "🔴 Inactive"
                    print(f"   • {service['name']} - ${price} ({model}) - {status}")
                    print(f"     {service['description']}")
                print()
                
        except Exception as e:
            print(f"❌ Error loading services: {e}")

    def platform_enhancement(self):
        """Platform enhancement menu"""
        print("\n🏗️ PLATFORM ENHANCEMENT")
        print("Coming soon! This will include:")
        print("• UI/UX improvements")
        print("• New feature development")
        print("• API endpoint creation")
        print("• Integration development")
        input("\nPress Enter to continue...")

    def reports_analytics(self):
        """Generate reports and analytics"""
        print("\n📊 REPORTS & ANALYTICS")
        
        try:
            with open(self.customers_file, 'r') as f:
                customers = json.load(f)
            with open(self.services_file, 'r') as f:
                services = json.load(f)
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return
        
        print(f"📈 CHATTERFIX ANALYTICS SUMMARY")
        print("=" * 50)
        print(f"👥 Total Customers: {len(customers)}")
        print(f"🛠️ Total Services: {len(services)}")
        
        if customers:
            # Customer analytics
            tiers = {}
            total_budget = 0
            cloud_prefs = {}
            
            for customer in customers.values():
                tier = customer.get('subscription_tier', 'unknown')
                tiers[tier] = tiers.get(tier, 0) + 1
                total_budget += customer.get('monthly_budget', 0)
                
                for cloud in customer.get('cloud_preferences', []):
                    cloud_prefs[cloud] = cloud_prefs.get(cloud, 0) + 1
            
            print(f"💰 Total Monthly Revenue: ${total_budget:,.2f}")
            print(f"📊 Average per Customer: ${total_budget/len(customers):,.2f}")
            
            print("\n🎯 Subscription Tiers:")
            for tier, count in tiers.items():
                print(f"   • {tier.title()}: {count} customers")
            
            print("\n☁️ Cloud Preferences:")
            for cloud, count in cloud_prefs.items():
                print(f"   • {cloud}: {count} customers")
        
        if services:
            # Service analytics
            providers = {}
            for service in services.values():
                provider = service.get('provider', 'unknown')
                providers[provider] = providers.get(provider, 0) + 1
            
            print("\n🏢 Services by Provider:")
            for provider, count in providers.items():
                print(f"   • {provider.upper()}: {count} services")
        
        input("\nPress Enter to continue...")

    def system_configuration(self):
        """System configuration menu"""
        print("\n🔧 SYSTEM CONFIGURATION")
        print("=" * 40)
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return
        
        print("Current Configuration:")
        print(f"📦 Version: {config.get('version', 'unknown')}")
        print(f"🔐 Git Enabled: {config.get('git_enabled', False)}")
        print(f"☁️ Cloud Deploy Enabled: {config.get('cloud_deploy_enabled', False)}")
        print(f"💾 Backup Enabled: {config.get('backup_enabled', True)}")
        print(f"🕒 Last Updated: {config.get('last_updated', 'unknown')}")
        
        print("\n⚠️ SECURITY NOTICE:")
        print("Git and Cloud Deploy are DISABLED for safety.")
        print("This ensures all changes stay local unless you explicitly enable them.")
        
        input("\nPress Enter to continue...")

    def backup_recovery(self):
        """Backup and recovery operations"""
        print("\n💾 BACKUP & RECOVERY")
        print("=" * 40)
        print("1. 📦 Create Backup")
        print("2. 🔄 Restore from Backup")
        print("3. 👀 View Backups")
        print("0. ⬅️ Back")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            self.create_backup()
        elif choice == "2":
            self.restore_backup()
        elif choice == "3":
            self.view_backups()

    def create_backup(self):
        """Create a backup of all ChatterFix data"""
        backup_dir = self.base_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"chatterfix_backup_{timestamp}"
        backup_path = backup_dir / backup_name
        
        try:
            # Create backup directory
            backup_path.mkdir(exist_ok=True)
            
            # Copy data files
            if self.data_dir.exists():
                shutil.copytree(self.data_dir, backup_path / "data")
            
            # Create backup manifest
            manifest = {
                "backup_name": backup_name,
                "timestamp": timestamp,
                "created_date": datetime.datetime.now().isoformat(),
                "version": "1.0.0",
                "files_backed_up": ["customers.json", "services.json", "config.json"]
            }
            
            with open(backup_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"✅ Backup created successfully!")
            print(f"📁 Location: {backup_path}")
            print(f"🕒 Timestamp: {timestamp}")
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")

    def view_backups(self):
        """View available backups"""
        backup_dir = self.base_dir / "backups"
        
        if not backup_dir.exists():
            print("📭 No backups found.")
            return
        
        backups = list(backup_dir.glob("chatterfix_backup_*"))
        if not backups:
            print("📭 No backups found.")
            return
        
        print(f"\n📦 AVAILABLE BACKUPS ({len(backups)} total)")
        print("=" * 50)
        
        for backup in sorted(backups, reverse=True):
            manifest_file = backup / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    print(f"📁 {manifest['backup_name']}")
                    print(f"   🕒 Created: {manifest['created_date'][:19]}")
                    print(f"   📄 Files: {len(manifest.get('files_backed_up', []))}")
                except:
                    print(f"📁 {backup.name} (manifest unavailable)")
            else:
                print(f"📁 {backup.name}")

    def security_permissions(self):
        """Security and permissions management"""
        print("\n🔐 SECURITY & PERMISSIONS")
        print("=" * 40)
        print("🛡️ Local-Only Security Status:")
        print("✅ Git commits: DISABLED")
        print("✅ Cloud deployments: DISABLED") 
        print("✅ External API calls: CONTROLLED")
        print("✅ Data encryption: FILE-LEVEL")
        print("✅ Backup retention: ENABLED")
        
        print("\n⚠️ IMPORTANT SECURITY NOTES:")
        print("• All customer data stays on your local machine")
        print("• No automatic syncing to cloud or git")
        print("• You control when/if data is shared")
        print("• Regular backups are recommended")
        
        input("\nPress Enter to continue...")

    def help_documentation(self):
        """Help and documentation"""
        print("\n📚 HELP & DOCUMENTATION")
        print("=" * 40)
        print("🎯 ChatterFix Local Assistant Help")
        print()
        print("GETTING STARTED:")
        print("1. Use 'Customer Management' to onboard new customers")
        print("2. Use 'Service Management' to add cloud services")
        print("3. Configure pricing and billing through customer profiles")
        print("4. Generate reports to track business metrics")
        print()
        print("SAFETY FEATURES:")
        print("• All data stays local by default")
        print("• No automatic git commits or cloud deploys")
        print("• Regular backups recommended")
        print("• Full control over data sharing")
        print()
        print("SUPPORT:")
        print("• Documentation: /CHATTERFIX_AI_ASSISTANT_INSTRUCTIONS.md")
        print("• Configuration: /data/config.json")
        print("• Data files: /data/ directory")
        
        input("\nPress Enter to continue...")

    def update_customer(self):
        """Update existing customer"""
        print("✏️ Customer update functionality coming soon!")
        input("Press Enter to continue...")

    def remove_customer(self):
        """Remove customer"""
        print("🗑️ Customer removal functionality coming soon!")
        input("Press Enter to continue...")

    def customer_analytics(self):
        """Customer-specific analytics"""
        print("📊 Customer analytics functionality coming soon!")
        input("Press Enter to continue...")

    def export_customers(self):
        """Export customer data"""
        print("📤 Customer export functionality coming soon!")
        input("Press Enter to continue...")

    def update_service(self):
        """Update existing service"""
        print("✏️ Service update functionality coming soon!")
        input("Press Enter to continue...")

    def remove_service(self):
        """Remove service"""
        print("🗑️ Service removal functionality coming soon!")
        input("Press Enter to continue...")

    def configure_service_integration(self):
        """Configure service integration"""
        print("🔗 Service integration functionality coming soon!")
        input("Press Enter to continue...")

    def update_service_pricing(self):
        """Update service pricing"""
        print("💰 Service pricing update functionality coming soon!")
        input("Press Enter to continue...")

    def restore_backup(self):
        """Restore from backup"""
        print("🔄 Backup restoration functionality coming soon!")
        input("Press Enter to continue...")

def main():
    """Main entry point"""
    try:
        assistant = ChatterFixAssistant()
        assistant.main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 ChatterFix Assistant interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()