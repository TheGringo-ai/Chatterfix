# ChatterFix CMMS - Complete User Guide

> **The Future of Maintenance Management: AI-First. Voice-Driven. Hands-Free.**

Welcome to ChatterFix, the world's first voice-first, AI-powered CMMS designed specifically for maintenance technicians. This comprehensive guide will help you master every feature of the application.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Work Order Management](#2-work-order-management)
3. [Asset Management](#3-asset-management)
4. [Inventory & Parts](#4-inventory--parts)
5. [Preventive Maintenance](#5-preventive-maintenance)
6. [AI Features & Fix-it-Fred](#6-ai-features--fix-it-fred)
7. [Analytics & Reporting](#7-analytics--reporting)
8. [Safety Features (SafetyFix)](#8-safety-features-safetyfix)
9. [Quality Features (QualityFix)](#9-quality-features-qualityfix)
10. [Team Management](#10-team-management)
11. [Mobile Usage](#11-mobile-usage)
12. [Tips & Best Practices](#12-tips--best-practices)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Getting Started

### 1.1 Creating an Account

1. Visit [https://chatterfix.com](https://chatterfix.com)
2. Click the **Sign Up Free** button in the top navigation
3. Fill in your details:
   - Username (unique identifier)
   - Email address
   - Full name
   - Password (minimum 8 characters with uppercase, lowercase, numbers, and special characters)
4. Click **Create Account**
5. Check your email for a verification link
6. Click the verification link to activate your account
7. You'll be automatically redirected to your dashboard

> **Pro Tip:** You can also try the demo mode without creating an account to explore features first.

### 1.2 Logging In

1. Go to [https://chatterfix.com/login](https://chatterfix.com/login)
2. Enter your email and password
3. Click **Sign In**
4. You'll be taken to your personalized dashboard

### 1.3 Understanding the Dashboard

Your dashboard shows:

| Widget | Description |
|--------|-------------|
| **Uptime %** | Overall equipment effectiveness |
| **Cost Saved** | Total savings from preventive maintenance |
| **Active WOs** | Current open work orders |
| **ROI** | Return on investment from AI optimization |
| **Stock Levels** | Inventory health percentage |
| **Training** | Available training modules |

**Navigation Menu:**
- **Dashboard** - Main overview
- **Work Orders** - Manage maintenance tasks
- **Assets** - Equipment tracking
- **Inventory** - Parts and supplies
- **Planner** - Scheduling and calendar
- **Analytics** - Reports and KPIs
- **Team** - User management
- **Purchasing** - Procurement
- **Training** - LineSmart learning
- **IoT Sensors** - Connected devices
- **AR Mode** - Augmented reality
- **Fix-it-Fred** - AI assistant

### 1.4 Using Voice Commands

ChatterFix is designed for hands-free operation. Here's how to use voice commands:

1. Click the **microphone icon** or say "Hey ChatterFix"
2. Speak your command naturally
3. Wait for the AI to process and respond

**Example Voice Commands:**
- "Create a work order for the hydraulic press, it's leaking oil"
- "Show me all open work orders"
- "What parts are low in stock?"
- "Check out 2 hydraulic seals for work order 1247"
- "What's the status of pump P-101?"

> **Pro Tip:** Speak naturally like you would to a colleague. The AI understands context and can fill in details automatically.

---

## 2. Work Order Management

### 2.1 Creating a Work Order (Manual)

1. Navigate to **Work Orders** in the menu
2. Click **Create New Work Order**
3. Fill in the form:
   - **Title**: Brief description of the issue
   - **Priority**: Low, Medium, High, or Critical
   - **Asset**: Select the affected equipment (optional)
   - **Work Type**: Corrective, Preventive, Emergency, or Inspection
   - **Description**: Detailed explanation
   - **Assigned To**: Select a technician
   - **Due Date**: Target completion date
4. Click **Create Work Order**

### 2.2 Creating a Work Order (Voice)

Simply say:
> "Hey ChatterFix, create a work order for [asset name], [describe the problem]"

**Example:**
> "Create a work order for HVAC Unit 3, it's not cooling properly and making a rattling noise"

ChatterFix will:
- Create the work order automatically
- Set appropriate priority based on the issue
- Link it to the correct asset
- Suggest parts that might be needed

### 2.3 Viewing Work Orders

1. Go to **Work Orders**
2. Use filters to find specific work orders:
   - **Status**: All, Open, In Progress, Completed
   - **Priority**: All, Critical, High, Medium, Low
   - **Search**: Text search by title or description

### 2.4 Updating Work Order Status

1. Click on a work order to open it
2. Update the status dropdown:
   - **Open** - Not yet started
   - **In Progress** - Currently being worked on
   - **On Hold** - Waiting for parts or approval
   - **Completed** - Work finished
   - **Cancelled** - No longer needed
3. Add notes about the work performed
4. Click **Save Changes**

### 2.5 Completing a Work Order

1. Open the work order
2. Click **Complete Work Order**
3. Enter completion details:
   - Labor hours spent
   - Parts used (auto-deducted from inventory)
   - Resolution notes
   - Before/after photos (optional)
4. Click **Submit Completion**

### 2.6 Bulk Importing Work Orders

1. Go to **Work Orders**
2. Click **Import**
3. Download the CSV template
4. Fill in your data following the template format
5. Upload the completed CSV file
6. Review the import preview
7. Click **Confirm Import**

---

## 3. Asset Management

### 3.1 Adding a New Asset

1. Navigate to **Assets**
2. Click **Create New Asset**
3. Fill in asset details:
   - **Asset Name**: Equipment name
   - **Asset Tag**: Unique identifier/barcode
   - **Serial Number**: Manufacturer's serial
   - **Model & Manufacturer**: Equipment specs
   - **Location**: Where it's installed
   - **Department**: Which team owns it
   - **Status**: Active, Maintenance Required, Down
   - **Criticality**: Low to Critical
   - **Purchase Date & Cost**: For tracking
   - **Warranty Expiry**: For alerts
4. Upload photos or documents
5. Click **Create Asset**

### 3.2 QR Code Scanning

**On Desktop:**
1. Go to **Assets**
2. Click **Scan Barcode**
3. Upload an image of the QR code or barcode

**On Mobile:**
1. Open ChatterFix on your phone
2. Tap the **Scan** icon
3. Point your camera at the asset's QR code
4. The asset details will load automatically

### 3.3 Asset Health Monitoring

Each asset shows:
- **Health Score** (0-100): AI-calculated equipment health
- **Condition Rating** (0-10): Manual assessment
- **Downtime Hours**: Total time out of service
- **Maintenance Costs**: Labor + parts costs
- **Risk Level**: Low, Medium, or High

### 3.4 AI Health Analysis

1. Open an asset's detail page
2. Click **AI Health Analysis**
3. ChatterFix AI will analyze:
   - Work order history
   - Maintenance patterns
   - Age and usage data
   - Part replacement history
4. You'll receive:
   - Current health score
   - Risk assessment
   - Recommendations for preventive action

### 3.5 Creating PM Schedules

1. Open an asset
2. Click **PM Schedules** tab
3. Click **Add PM Schedule**
4. Configure:
   - **Schedule Name**: What maintenance task
   - **Type**: Time-based, Usage-based, or Condition-based
   - **Interval**: Every X days/hours/cycles
   - **Priority**: Task urgency
   - **Estimated Duration**: Hours to complete
   - **Instructions**: Step-by-step procedure
5. Click **Save Schedule**

### 3.6 AI-Generated PM Recommendations

1. Open an asset
2. Click **Generate PM with AI**
3. Upload relevant documentation (manuals, specs)
4. AI will analyze and create comprehensive PM schedules based on:
   - Manufacturer recommendations
   - Industry best practices
   - Your historical data
   - Similar asset patterns

---

## 4. Inventory & Parts

### 4.1 Viewing Inventory

1. Navigate to **Inventory**
2. Browse parts in grid or list view
3. Each part shows:
   - Part number and name
   - Current stock level
   - Stock status (In Stock, Low, Out of Stock)
   - Location in warehouse
   - Unit cost

### 4.2 Adding Parts

1. Go to **Inventory**
2. Click **Add Part**
3. Enter part information:
   - Part number
   - Name and description
   - Category
   - Location (shelf/bin)
   - Current stock quantity
   - Minimum stock level
   - Unit cost
   - Vendor
4. Upload part image (optional)
5. Click **Save Part**

### 4.3 Checking Out Parts

**Manual Checkout:**
1. Go to **Inventory**
2. Find the part
3. Click **Quick Checkout**
4. Enter quantity
5. Select work order (optional)
6. Click **Checkout**

**Voice Checkout:**
> "Check out 3 air filters for work order 1234"

### 4.4 Checking In Parts

1. Go to **Inventory**
2. Find the part
3. Click **Check In**
4. Enter quantity received
5. Update location if needed
6. Click **Confirm**

### 4.5 Low Stock Alerts

ChatterFix automatically monitors inventory and alerts you when:
- Stock falls below minimum level
- Parts are completely out of stock
- Reorder points are reached

View alerts in:
- Dashboard notifications
- Inventory page (red badges)
- Email notifications (if enabled)

### 4.6 Vendor Management

1. Go to **Inventory** > **Vendors**
2. Click **Add Vendor**
3. Enter vendor details:
   - Company name
   - Contact information
   - Payment terms
   - Associated parts
4. Track vendor performance over time

---

## 5. Preventive Maintenance

### 5.1 Understanding PM Types

| Type | Trigger | Example |
|------|---------|---------|
| **Time-based** | Calendar interval | "Every 30 days" |
| **Usage-based** | Operating hours/cycles | "Every 500 hours" |
| **Condition-based** | Sensor thresholds | "When vibration > 5mm/s" |

### 5.2 Recording Meter Readings

1. Open an asset
2. Click **Record Meter Reading**
3. Enter current value (hours, cycles, etc.)
4. Click **Submit**

ChatterFix will automatically:
- Track usage trends
- Trigger PMs when thresholds are met
- Generate work orders as needed

### 5.3 PM Compliance Tracking

View PM compliance in **Analytics** > **PM Compliance**:
- Completion rates
- Overdue PMs
- Upcoming schedules
- Compliance trends

---

## 6. AI Features & Fix-it-Fred

### 6.1 Fix-it-Fred AI Assistant

Fix-it-Fred is your AI maintenance expert. Access it by:
- Clicking the **Fix-it-Fred** icon in the menu
- Using voice commands
- Clicking the chat bubble on any page

**What Fix-it-Fred Can Do:**
- Diagnose equipment problems
- Suggest troubleshooting steps
- Create work orders from conversation
- Look up part information
- Provide maintenance recommendations
- Answer questions about procedures

### 6.2 AI Troubleshooting

1. Describe the problem to Fix-it-Fred
2. Provide additional context when asked
3. Receive step-by-step diagnosis
4. Get repair recommendations
5. Create a work order directly from the chat

**Example Conversation:**
> You: "The hydraulic press is making a grinding noise when it cycles"
>
> Fix-it-Fred: "A grinding noise during cycling typically indicates worn bearings or contaminated hydraulic fluid. Let me ask a few questions:
> 1. When did the noise start?
> 2. Is there any visible fluid leak?
> 3. What's the current operating pressure?"

### 6.3 AI Team Collaboration

ChatterFix uses multiple AI models for best results:
- **GPT-4 Analyst** - Complex reasoning and analysis
- **ChatGPT Coder** - Technical solutions
- **Gemini Creative** - Innovative approaches
- **Gemini Analyst** - Data analysis
- **Grok Coder** - Fast solutions
- **Grok Reasoner** - Strategic thinking

For complex issues, the AI team collaborates to provide the best answer.

### 6.4 Computer Vision Features

ChatterFix can analyze images for:
- **Asset Condition**: Upload a photo for AI analysis
- **Part Recognition**: Identify parts from photos
- **Text Extraction**: OCR from labels and documents
- **Defect Detection**: Quality inspection

---

## 7. Analytics & Reporting

### 7.1 Dashboard Metrics

| Metric | Description |
|--------|-------------|
| **MTTR** | Mean Time To Repair - average repair duration |
| **MTBF** | Mean Time Between Failures - reliability measure |
| **PM Compliance** | Percentage of PMs completed on time |
| **Work Order Completion** | Tasks completed vs. assigned |
| **Cost per Asset** | Maintenance spending by equipment |

### 7.2 Accessing Reports

1. Go to **Analytics**
2. Select report type:
   - KPI Summary
   - Work Order Analytics
   - Asset Reliability
   - Cost Analysis
   - Technician Performance

### 7.3 Exporting Reports

1. Open the desired report
2. Click **Export**
3. Choose format:
   - **CSV** - For spreadsheets
   - **PDF** - For printing/sharing
   - **Excel** - For data analysis
4. Download the file

### 7.4 Custom Date Ranges

1. Click the date picker
2. Select start and end dates
3. Click **Apply**
4. Charts and data update automatically

---

## 8. Safety Features (SafetyFix)

### 8.1 Reporting Safety Incidents

1. Go to **SafetyFix** > **Report Incident**
2. Or use voice: "Report a safety incident"
3. Select incident type:
   - Near-miss
   - Injury
   - Equipment failure
   - Environmental hazard
4. Provide details and photos
5. Submit the report

### 8.2 PPE Compliance Checking

1. Take a photo at the worksite
2. Upload to **SafetyFix** > **PPE Check**
3. AI analyzes for required PPE:
   - Hard hat
   - Safety glasses
   - High-visibility vest
   - Safety harness
   - Steel-toe boots
   - Gloves
   - Ear protection
4. Get instant compliance feedback

### 8.3 Safety Dashboard

View safety metrics:
- Incident frequency
- Near-miss trends
- PPE compliance rates
- Hazard reports
- Safety training completion

---

## 9. Quality Features (QualityFix)

### 9.1 Visual QA Inspections

1. Go to **QualityFix** > **Visual QA**
2. Upload reference image (golden sample)
3. Upload actual part image
4. AI compares and detects:
   - Scratches
   - Dents
   - Dimensional issues
   - Contamination
   - Assembly errors
   - Finish defects
5. Review defect report with severity ratings

### 9.2 Non-Conformance Reporting

1. Go to **QualityFix** > **Non-Conformance**
2. Click **New Report**
3. Document:
   - Defect type
   - Severity
   - Affected items
   - Root cause (if known)
4. Get AI-recommended disposition

### 9.3 CAPA Management

1. Go to **QualityFix** > **CAPA**
2. Create new CAPA from non-conformance
3. Document:
   - Root cause analysis
   - Corrective actions
   - Preventive measures
   - Target completion dates
4. Track through implementation
5. Verify effectiveness

---

## 10. Team Management

### 10.1 Inviting Team Members

1. Go to **Settings** > **Team**
2. Click **Invite Member**
3. Enter their email address
4. Select role:
   - **Admin** - Full access
   - **Manager** - Manage team and reports
   - **Technician** - Work orders and assets
   - **Purchaser** - Inventory and procurement
   - **Viewer** - Read-only access
5. Click **Send Invitation**

### 10.2 Managing Roles

1. Go to **Settings** > **Team**
2. Click on a team member
3. Update their role as needed
4. Click **Save**

### 10.3 Team Performance

View in **Analytics** > **Technician Performance**:
- Work orders completed
- Average completion time
- First-time fix rate
- Training progress

---

## 11. Mobile Usage

### 11.1 Mobile Interface

ChatterFix is fully responsive. On mobile:
- Bottom navigation for quick access
- Swipe gestures for navigation
- Touch-optimized buttons
- Camera integration for scanning

### 11.2 QR Scanning on Mobile

1. Tap the **Scan** button
2. Point camera at QR code
3. Asset loads instantly
4. View details, create work orders, or check out parts

### 11.3 Offline Capabilities

Some features work offline:
- View recently accessed work orders
- View asset information
- Draft new work orders (sync when online)

> **Note:** Full functionality requires internet connection.

---

## 12. Tips & Best Practices

### Voice Command Tips

| Instead of... | Say... |
|---------------|--------|
| "Create work order" | "Create a work order for [asset] because [problem]" |
| "Find part" | "Do we have [part name] in stock?" |
| "Status" | "What's the status of work order [number]?" |

### Efficiency Tips

1. **Use QR codes** - Scan instead of searching
2. **Set up PM schedules** - Prevent breakdowns
3. **Link parts to assets** - Faster checkout
4. **Use voice commands** - Hands-free operation
5. **Check dashboards daily** - Stay proactive
6. **Export reports weekly** - Track trends

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + N` | New work order |
| `Ctrl + F` | Search |
| `Ctrl + S` | Save |
| `/` | Open command palette |

---

## 13. Troubleshooting

### Common Issues

**Problem: Voice commands not working**
- Check microphone permissions in browser
- Ensure you're in a quiet environment
- Try refreshing the page

**Problem: QR code not scanning**
- Clean camera lens
- Ensure good lighting
- Hold camera steady
- Try uploading image instead

**Problem: Work order won't save**
- Check required fields are filled
- Verify internet connection
- Try refreshing the page

**Problem: Can't check out parts**
- Verify stock is available
- Check user permissions
- Ensure work order exists (if linking)

### Getting Help

- **Help Center**: [https://chatterfix.com/help](https://chatterfix.com/help)
- **Email Support**: support@chatterfix.com
- **In-App Chat**: Click the help icon in the bottom right

---

## Quick Reference Card

### Voice Commands Cheat Sheet

```
Work Orders:
- "Create work order for [asset], [problem]"
- "Show open work orders"
- "Complete work order [number]"
- "Assign work order [number] to [technician]"

Assets:
- "Show asset [name or tag]"
- "What's the health of [asset]?"
- "Create PM schedule for [asset]"

Inventory:
- "Check out [quantity] [part] for WO [number]"
- "What's in stock?"
- "Low stock report"

General:
- "Dashboard"
- "Show my tasks"
- "Help with [topic]"
```

---

**Thank you for choosing ChatterFix!**

*The Future of Maintenance Management is Here.*

---

*Document Version: 2.2.0*
*Last Updated: January 2026*
*Copyright 2026 ChatterFix - All Rights Reserved*
