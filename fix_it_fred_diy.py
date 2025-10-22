#!/usr/bin/env python3
"""
🔧 Fix-It Fred DIY Tech Assistant
Standalone app for DIY homeowners and small businesses
Features: Job planning, parts lists, maintenance reminders, service scheduling
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Fix-It Fred DIY Tech Assistant",
    description="Your personal DIY helper for home and small business maintenance",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_database():
    """Initialize SQLite database for DIY data"""
    conn = sqlite3.connect('fix_it_fred_diy.db')
    cursor = conn.cursor()
    
    # Jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            difficulty TEXT DEFAULT 'medium',
            estimated_time TEXT,
            status TEXT DEFAULT 'planned',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date DATE,
            completed_at TIMESTAMP
        )
    ''')
    
    # Parts/Materials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            quantity INTEGER DEFAULT 1,
            unit_cost REAL DEFAULT 0.0,
            where_to_buy TEXT,
            part_number TEXT,
            category TEXT DEFAULT 'general',
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    ''')
    
    # Maintenance reminders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            frequency_days INTEGER NOT NULL,
            last_completed DATE,
            next_due DATE,
            category TEXT DEFAULT 'general',
            priority TEXT DEFAULT 'medium',
            auto_schedule BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Instructions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            step_number INTEGER,
            instruction TEXT NOT NULL,
            safety_note TEXT,
            tools_needed TEXT,
            estimated_minutes INTEGER,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    ''')
    
    # Service history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            reminder_id INTEGER,
            service_date DATE NOT NULL,
            technician TEXT,
            cost REAL,
            notes TEXT,
            photos TEXT,
            next_service_due DATE,
            FOREIGN KEY (job_id) REFERENCES jobs (id),
            FOREIGN KEY (reminder_id) REFERENCES maintenance_reminders (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Pydantic models
class Job(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = "general"
    difficulty: Optional[str] = "medium"
    estimated_time: Optional[str] = ""
    due_date: Optional[str] = None

class Part(BaseModel):
    name: str
    description: Optional[str] = ""
    quantity: Optional[int] = 1
    unit_cost: Optional[float] = 0.0
    where_to_buy: Optional[str] = ""
    part_number: Optional[str] = ""
    category: Optional[str] = "general"

class MaintenanceReminder(BaseModel):
    title: str
    description: Optional[str] = ""
    frequency_days: int
    category: Optional[str] = "general"
    priority: Optional[str] = "medium"
    auto_schedule: Optional[bool] = False

class Instruction(BaseModel):
    step_number: int
    instruction: str
    safety_note: Optional[str] = ""
    tools_needed: Optional[str] = ""
    estimated_minutes: Optional[int] = 15

# Database helper functions
def get_db_connection():
    return sqlite3.connect('fix_it_fred_diy.db')

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the Fix-It Fred DIY interface"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fix-It Fred DIY Tech Assistant</title>
    
    <!-- PWA Meta Tags -->
    <meta name="application-name" content="Fix-It Fred DIY">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Fix-It Fred">
    <meta name="description" content="Your personal DIY helper for home and small business maintenance">
    <meta name="format-detection" content="telephone=no">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#28a745">
    
    <!-- PWA Links -->
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%2328a745'/%3E%3Ctext x='50' y='55' font-family='Arial,sans-serif' font-size='30' fill='white' text-anchor='middle'%3E🔧%3C/text%3E%3C/svg%3E">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #2E86AB;
            --success-color: #A23B72;
            --warning-color: #F18F01;
            --danger-color: #C73E1D;
        }
        
        .navbar {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--success-color) 100%);
        }
        
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 0;
        }
        
        .feature-card {
            border: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
            margin-bottom: 20px;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .section-header {
            margin: 40px 0 30px 0;
            text-align: center;
        }
        
        .job-card {
            border-left: 4px solid var(--primary-color);
            margin-bottom: 15px;
        }
        
        .reminder-card {
            border-left: 4px solid var(--warning-color);
            margin-bottom: 15px;
        }
        
        .difficulty-easy { color: var(--success-color); }
        .difficulty-medium { color: var(--warning-color); }
        .difficulty-hard { color: var(--danger-color); }
        
        .chat-container {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .message {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 10px;
        }
        
        .message.user {
            background-color: #e3f2fd;
            margin-left: 20%;
        }
        
        .message.fred {
            background-color: #f5f5f5;
            margin-right: 20%;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fas fa-tools me-2"></i>Fix-It Fred DIY
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#jobs">Jobs</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#reminders">Reminders</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#chat">Chat with Fred</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section">
        <div class="container text-center">
            <h1 class="display-4 mb-4">
                <i class="fas fa-robot me-3"></i>Fix-It Fred DIY Assistant
            </h1>
            <p class="lead mb-4">Your personal AI tech helper for home and small business maintenance</p>
            <div class="row">
                <div class="col-md-3">
                    <div class="text-center">
                        <i class="fas fa-clipboard-list fa-3x mb-3"></i>
                        <h5>Plan Jobs</h5>
                        <p>Get step-by-step instructions for any repair or maintenance task</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <i class="fas fa-shopping-cart fa-3x mb-3"></i>
                        <h5>Parts Lists</h5>
                        <p>Automatic parts and materials lists with cost estimates</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <i class="fas fa-bell fa-3x mb-3"></i>
                        <h5>Reminders</h5>
                        <p>Never miss furnace filter changes, oil changes, or service dates</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <i class="fas fa-calendar-alt fa-3x mb-3"></i>
                        <h5>Scheduling</h5>
                        <p>Smart scheduling for maintenance and service appointments</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Jobs Section -->
    <section id="jobs" class="container">
        <div class="section-header">
            <h2><i class="fas fa-wrench me-2"></i>Current Jobs</h2>
            <button class="btn btn-primary" onclick="showNewJobModal()">
                <i class="fas fa-plus me-2"></i>Plan New Job
            </button>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <div id="jobs-list">
                    <!-- Jobs will be loaded here -->
                </div>
            </div>
            <div class="col-md-4">
                <div class="card feature-card">
                    <div class="card-header">
                        <h5><i class="fas fa-lightbulb me-2"></i>Quick Job Ideas</h5>
                    </div>
                    <div class="card-body">
                        <div class="list-group list-group-flush">
                            <a href="#" class="list-group-item list-group-item-action" onclick="quickJob('furnace-filter')">
                                Change Furnace Filter
                            </a>
                            <a href="#" class="list-group-item list-group-item-action" onclick="quickJob('oil-change')">
                                Vehicle Oil Change
                            </a>
                            <a href="#" class="list-group-item list-group-item-action" onclick="quickJob('faucet-repair')">
                                Fix Leaky Faucet
                            </a>
                            <a href="#" class="list-group-item list-group-item-action" onclick="quickJob('gutter-cleaning')">
                                Clean Gutters
                            </a>
                            <a href="#" class="list-group-item list-group-item-action" onclick="quickJob('smoke-detector')">
                                Replace Smoke Detector Battery
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Maintenance Reminders Section -->
    <section id="reminders" class="container">
        <div class="section-header">
            <h2><i class="fas fa-bell me-2"></i>Maintenance Reminders</h2>
            <button class="btn btn-warning" onclick="showNewReminderModal()">
                <i class="fas fa-plus me-2"></i>Add Reminder
            </button>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <div id="reminders-list">
                    <!-- Reminders will be loaded here -->
                </div>
            </div>
            <div class="col-md-4">
                <div class="card feature-card">
                    <div class="card-header">
                        <h5><i class="fas fa-clock me-2"></i>Overdue Items</h5>
                    </div>
                    <div class="card-body">
                        <div id="overdue-list">
                            <!-- Overdue items will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Chat with Fred Section -->
    <section id="chat" class="container">
        <div class="section-header">
            <h2><i class="fas fa-robot me-2"></i>Chat with Fix-It Fred</h2>
        </div>
        
        <div class="row">
            <div class="col-md-8 mx-auto">
                <div class="card feature-card">
                    <div class="card-header">
                        <h5>Ask Fred about any DIY project or maintenance question</h5>
                    </div>
                    <div class="card-body">
                        <div class="chat-container" id="chat-messages">
                            <div class="message fred">
                                <strong>Fix-It Fred:</strong> Hi there! I'm here to help with your DIY projects and maintenance needs. What can I help you with today?
                            </div>
                        </div>
                        <div class="input-group">
                            <input type="text" class="form-control" id="chat-input" 
                                   placeholder="Ask about repairs, maintenance, parts, or schedules..."
                                   onkeypress="handleChatKeypress(event)">
                            <button class="btn btn-primary" onclick="sendMessage()">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Application state
        let jobs = [];
        let reminders = [];
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadJobs();
            loadReminders();
            checkOverdueItems();
        });
        
        // Load jobs from API
        async function loadJobs() {
            try {
                const response = await fetch('/api/jobs');
                jobs = await response.json();
                displayJobs();
            } catch (error) {
                console.error('Error loading jobs:', error);
            }
        }
        
        // Display jobs in the UI
        function displayJobs() {
            const container = document.getElementById('jobs-list');
            if (jobs.length === 0) {
                container.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        No jobs planned yet. Click "Plan New Job" to get started!
                    </div>
                `;
                return;
            }
            
            container.innerHTML = jobs.map(job => `
                <div class="card job-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h5 class="card-title">${job.title}</h5>
                                <p class="card-text">${job.description || ''}</p>
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>${job.estimated_time || 'Time not estimated'}
                                    <span class="ms-3 difficulty-${job.difficulty}">
                                        <i class="fas fa-signal me-1"></i>${job.difficulty} difficulty
                                    </span>
                                </small>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-${getStatusColor(job.status)}">${job.status}</span>
                                <div class="btn-group mt-2" role="group">
                                    <button class="btn btn-sm btn-outline-primary" onclick="viewJob(${job.id})">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-success" onclick="markComplete(${job.id})">
                                        <i class="fas fa-check"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        // Load reminders from API
        async function loadReminders() {
            try {
                const response = await fetch('/api/reminders');
                reminders = await response.json();
                displayReminders();
            } catch (error) {
                console.error('Error loading reminders:', error);
            }
        }
        
        // Display reminders in the UI
        function displayReminders() {
            const container = document.getElementById('reminders-list');
            if (reminders.length === 0) {
                container.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        No maintenance reminders set up yet. Click "Add Reminder" to get started!
                    </div>
                `;
                return;
            }
            
            container.innerHTML = reminders.map(reminder => `
                <div class="card reminder-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h5 class="card-title">${reminder.title}</h5>
                                <p class="card-text">${reminder.description || ''}</p>
                                <small class="text-muted">
                                    <i class="fas fa-repeat me-1"></i>Every ${reminder.frequency_days} days
                                    <span class="ms-3">
                                        <i class="fas fa-calendar me-1"></i>Next due: ${reminder.next_due || 'Not scheduled'}
                                    </span>
                                </small>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-${getPriorityColor(reminder.priority)}">${reminder.priority}</span>
                                <div class="btn-group mt-2" role="group">
                                    <button class="btn btn-sm btn-outline-success" onclick="markReminderComplete(${reminder.id})">
                                        <i class="fas fa-check"></i> Done
                                    </button>
                                    <button class="btn btn-sm btn-outline-primary" onclick="scheduleReminder(${reminder.id})">
                                        <i class="fas fa-calendar-plus"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        // Check for overdue items
        function checkOverdueItems() {
            // This would check for overdue reminders and display them
            const overdueContainer = document.getElementById('overdue-list');
            overdueContainer.innerHTML = `
                <div class="alert alert-success alert-sm">
                    <i class="fas fa-check-circle me-2"></i>
                    All caught up! No overdue items.
                </div>
            `;
        }
        
        // Quick job creation
        function quickJob(jobType) {
            const quickJobs = {
                'furnace-filter': {
                    title: 'Change Furnace Filter',
                    description: 'Replace the HVAC furnace filter for better air quality and efficiency',
                    category: 'hvac',
                    difficulty: 'easy',
                    estimated_time: '15 minutes'
                },
                'oil-change': {
                    title: 'Vehicle Oil Change',
                    description: 'Change engine oil and oil filter for vehicle maintenance',
                    category: 'automotive',
                    difficulty: 'medium', 
                    estimated_time: '45 minutes'
                },
                'faucet-repair': {
                    title: 'Fix Leaky Faucet',
                    description: 'Repair dripping faucet by replacing washers or cartridge',
                    category: 'plumbing',
                    difficulty: 'medium',
                    estimated_time: '30 minutes'
                },
                'gutter-cleaning': {
                    title: 'Clean Gutters',
                    description: 'Remove debris and check for proper drainage',
                    category: 'exterior',
                    difficulty: 'medium',
                    estimated_time: '2 hours'
                },
                'smoke-detector': {
                    title: 'Replace Smoke Detector Battery',
                    description: 'Change batteries in all smoke detectors for safety',
                    category: 'safety',
                    difficulty: 'easy',
                    estimated_time: '10 minutes'
                }
            };
            
            const jobData = quickJobs[jobType];
            if (jobData) {
                createJob(jobData);
            }
        }
        
        // Create new job
        async function createJob(jobData) {
            try {
                const response = await fetch('/api/jobs', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(jobData)
                });
                
                if (response.ok) {
                    loadJobs(); // Reload jobs list
                    // Show success message or instructions
                    showJobInstructions(jobData);
                }
            } catch (error) {
                console.error('Error creating job:', error);
            }
        }
        
        // Show job instructions
        function showJobInstructions(jobData) {
            addChatMessage('fred', `Great! I've added "${jobData.title}" to your job list. Here are the basic steps and what you'll need:`);
            
            // This would fetch detailed instructions from the AI
            setTimeout(() => {
                addChatMessage('fred', getJobInstructions(jobData));
            }, 1000);
        }
        
        // Get job instructions (this would use AI in real implementation)
        function getJobInstructions(jobData) {
            const instructions = {
                'furnace-filter': `
                    <strong>Steps for Furnace Filter Change:</strong><br>
                    1. Turn off HVAC system<br>
                    2. Locate filter compartment (usually near furnace)<br>
                    3. Note airflow direction arrow on old filter<br>
                    4. Remove old filter and dispose properly<br>
                    5. Insert new filter with airflow arrow pointing same direction<br>
                    6. Turn system back on<br><br>
                    <strong>Parts needed:</strong> HVAC filter (check size: 16x20x1, 20x25x1, etc.)<br>
                    <strong>Tools:</strong> None usually required<br>
                    <strong>Cost:</strong> $5-15 for filter
                `,
                'oil-change': `
                    <strong>Steps for Oil Change:</strong><br>
                    1. Warm up engine (2-3 minutes)<br>
                    2. Raise vehicle safely with jack and stands<br>
                    3. Locate drain plug under oil pan<br>
                    4. Place drain pan under plug<br>
                    5. Remove drain plug with wrench<br>
                    6. Let oil drain completely (15-20 minutes)<br>
                    7. Replace drain plug with new gasket<br>
                    8. Remove old oil filter<br>
                    9. Install new filter with thin coat of oil on gasket<br>
                    10. Lower vehicle and add new oil through filler cap<br>
                    11. Check level with dipstick<br><br>
                    <strong>Parts needed:</strong> Motor oil (check manual for type/amount), oil filter, drain plug gasket<br>
                    <strong>Tools:</strong> Socket wrench, oil filter wrench, drain pan, funnel<br>
                    <strong>Safety:</strong> Ensure vehicle is stable on jack stands
                `
            };
            
            return instructions[Object.keys(instructions).find(key => jobData.title.includes(key))] || 
                   'Instructions will be provided when you start this job. Click "View Job" for detailed steps.';
        }
        
        // Chat functionality
        function handleChatKeypress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            addChatMessage('user', message);
            input.value = '';
            
            // Simulate AI response
            setTimeout(() => {
                const response = getFredResponse(message);
                addChatMessage('fred', response);
            }, 1000);
        }
        
        function addChatMessage(sender, message) {
            const container = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'Fix-It Fred'}:</strong> ${message}`;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        // Simple AI response simulation (would use real AI in production)
        function getFredResponse(message) {
            const lowerMessage = message.toLowerCase();
            
            if (lowerMessage.includes('furnace') || lowerMessage.includes('filter')) {
                return "For furnace filter changes, I recommend checking/changing every 1-3 months depending on usage. Look for the size printed on the old filter frame (like 16x20x1). Would you like me to set up a reminder for this?";
            } else if (lowerMessage.includes('oil change')) {
                return "Oil changes are typically needed every 3,000-7,500 miles depending on your vehicle and oil type. Check your owner's manual for specifics. I can help you plan this job and create a parts list. What's your vehicle make and model?";
            } else if (lowerMessage.includes('leak') || lowerMessage.includes('faucet')) {
                return "For leaky faucets, the most common causes are worn washers, O-rings, or cartridges. First, turn off the water supply under the sink. What type of faucet do you have - single handle, double handle, or pull-out spray?";
            } else if (lowerMessage.includes('reminder') || lowerMessage.includes('schedule')) {
                return "I can help set up maintenance reminders for any regular tasks! Common ones include: furnace filters (monthly), oil changes (every 3-6 months), smoke detector batteries (annually), and seasonal tasks. What would you like to be reminded about?";
            } else if (lowerMessage.includes('parts') || lowerMessage.includes('buy')) {
                return "I can generate parts lists with estimated costs and where to buy them. For most home improvement projects, I'll suggest hardware stores like Home Depot, Lowe's, or local suppliers. What project are you working on?";
            } else {
                return "I'm here to help with any DIY project, maintenance task, or repair question! I can provide step-by-step instructions, parts lists, safety tips, and set up reminders. What specific project or issue are you dealing with?";
            }
        }
        
        // Utility functions
        function getStatusColor(status) {
            switch(status) {
                case 'completed': return 'success';
                case 'in-progress': return 'warning';
                case 'planned': return 'primary';
                default: return 'secondary';
            }
        }
        
        function getPriorityColor(priority) {
            switch(priority) {
                case 'high': return 'danger';
                case 'medium': return 'warning';
                case 'low': return 'success';
                default: return 'secondary';
            }
        }
        
        // Placeholder functions for modals and actions
        function showNewJobModal() {
            // Would open a modal for creating new jobs
            alert('Job creation modal would open here. For now, try the Quick Job buttons!');
        }
        
        function showNewReminderModal() {
            // Would open a modal for creating new reminders
            alert('Reminder creation modal would open here. Chat with Fred to set up reminders!');
        }
        
        function viewJob(id) {
            alert(`Would show detailed view of job ${id} with instructions and parts list`);
        }
        
        function markComplete(id) {
            alert(`Would mark job ${id} as complete and ask for notes/photos`);
        }
        
        function markReminderComplete(id) {
            alert(`Would mark reminder ${id} as complete and schedule next occurrence`);
        }
        
        function scheduleReminder(id) {
            alert(`Would open calendar to schedule reminder ${id}`);
        }

        // PWA Service Worker Registration
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then((registration) => {
                        console.log('Fix-It Fred SW: Service Worker registered successfully');
                        
                        // Check for updates
                        registration.addEventListener('updatefound', () => {
                            const newWorker = registration.installing;
                            newWorker.addEventListener('statechange', () => {
                                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                    showUpdateNotification();
                                }
                            });
                        });
                    })
                    .catch((error) => {
                        console.log('Fix-It Fred SW: Service Worker registration failed:', error);
                    });
            });
        }

        // PWA Install Prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            showInstallButton();
        });

        function showInstallButton() {
            const installBanner = document.createElement('div');
            installBanner.className = 'alert alert-success alert-dismissible position-fixed top-0 start-50 translate-middle-x mt-3';
            installBanner.style.zIndex = '9999';
            installBanner.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas fa-download me-2"></i>
                    <span>Install Fix-It Fred for offline DIY assistance</span>
                    <button class="btn btn-sm btn-success ms-3" onclick="installPWA()">Install</button>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            document.body.appendChild(installBanner);
        }

        function installPWA() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('User accepted the install prompt');
                    }
                    deferredPrompt = null;
                });
            }
        }

        function showUpdateNotification() {
            const updateBanner = document.createElement('div');
            updateBanner.className = 'alert alert-warning position-fixed bottom-0 start-50 translate-middle-x mb-3';
            updateBanner.style.zIndex = '9999';
            updateBanner.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas fa-sync-alt me-2"></i>
                    <span>A new version of Fix-It Fred is available</span>
                    <button class="btn btn-sm btn-warning ms-3" onclick="updateApp()">Update</button>
                </div>
            `;
            document.body.appendChild(updateBanner);
        }

        function updateApp() {
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.getRegistrations().then((registrations) => {
                    registrations.forEach((registration) => {
                        registration.update().then(() => {
                            window.location.reload();
                        });
                    });
                });
            }
        }

        // Add to global scope for PWA functions
        window.installPWA = installPWA;
        window.updateApp = updateApp;
    </script>
</body>
</html>
    """

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fix-it-fred-diy", "version": "1.0.0"}

@app.get("/manifest.json")
async def manifest():
    """PWA Manifest for Fix-It Fred DIY"""
    return {
        "name": "Fix-It Fred DIY Assistant",
        "short_name": "Fix-It Fred",
        "description": "Your personal DIY helper for home and small business maintenance",
        "version": "1.0.0",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#28a745",
        "theme_color": "#28a745",
        "orientation": "portrait-primary",
        "scope": "/",
        "icons": [
            {
                "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%2328a745'/%3E%3Ctext x='50' y='55' font-family='Arial,sans-serif' font-size='30' fill='white' text-anchor='middle'%3E🔧%3C/text%3E%3C/svg%3E",
                "sizes": "192x192",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            },
            {
                "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%2328a745'/%3E%3Ctext x='50' y='55' font-family='Arial,sans-serif' font-size='30' fill='white' text-anchor='middle'%3E🔧%3C/text%3E%3C/svg%3E",
                "sizes": "512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ],
        "categories": ["utilities", "productivity", "lifestyle"],
        "shortcuts": [
            {
                "name": "DIY Jobs",
                "url": "/jobs?utm_source=pwa_shortcut",
                "description": "View and create DIY jobs"
            },
            {
                "name": "Parts List",
                "url": "/parts?utm_source=pwa_shortcut",
                "description": "Manage parts and materials"
            },
            {
                "name": "Reminders",
                "url": "/reminders?utm_source=pwa_shortcut",
                "description": "View maintenance reminders"
            }
        ]
    }

@app.get("/sw.js")
async def service_worker():
    """Service Worker for PWA functionality"""
    sw_content = '''
/**
 * Fix-It Fred DIY PWA Service Worker
 * Enables offline functionality for DIY assistance
 */

const CACHE_NAME = 'fixit-fred-v1-0';
const STATIC_CACHE = 'fixit-fred-static-v1';
const DYNAMIC_CACHE = 'fixit-fred-dynamic-v1';

// Static resources to cache
const STATIC_RESOURCES = [
  '/',
  '/manifest.json',
  '/jobs',
  '/parts',
  '/reminders',
  '/instructions',
  '/chat'
];

// Install event
self.addEventListener('install', (event) => {
  console.log('Fix-It Fred SW: Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(STATIC_RESOURCES))
      .then(() => self.skipWaiting())
  );
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Fix-It Fred SW: Activating...');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event
self.addEventListener('fetch', (event) => {
  if (event.request.method === 'GET') {
    event.respondWith(handleGetRequest(event.request));
  }
});

async function handleGetRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for HTML requests
    if (request.headers.get('Accept')?.includes('text/html')) {
      return new Response(generateOfflinePage(), {
        status: 200,
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    return new Response('Offline', { status: 503 });
  }
}

function generateOfflinePage() {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Fix-It Fred - Offline</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #28a745; color: white; }
        .offline-container { background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px; max-width: 400px; margin: 0 auto; }
      </style>
    </head>
    <body>
      <div class="offline-container">
        <h1>🔧 Fix-It Fred</h1>
        <p>You're offline! Some features may not be available.</p>
        <button onclick="window.location.reload()">Try Again</button>
      </div>
    </body>
    </html>
  `;
}
    '''
    return Response(content=sw_content, media_type="application/javascript")

# Jobs API
@app.get("/api/jobs")
async def get_jobs():
    """Get all jobs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    jobs = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    return jobs

@app.post("/api/jobs")
async def create_job(job: Job):
    """Create a new job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (title, description, category, difficulty, estimated_time, due_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (job.title, job.description, job.category, job.difficulty, job.estimated_time, job.due_date))
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "job_id": job_id}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: int):
    """Get specific job with instructions and parts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get job details
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_dict = dict(zip([col[0] for col in cursor.description], job))
    
    # Get instructions
    cursor.execute("SELECT * FROM instructions WHERE job_id = ? ORDER BY step_number", (job_id,))
    instructions = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    # Get parts
    cursor.execute("SELECT * FROM parts WHERE job_id = ?", (job_id,))
    parts = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "job": job_dict,
        "instructions": instructions,
        "parts": parts
    }

# Parts API
@app.post("/api/jobs/{job_id}/parts")
async def add_job_part(job_id: int, part: Part):
    """Add a part to a job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parts (job_id, name, description, quantity, unit_cost, where_to_buy, part_number, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (job_id, part.name, part.description, part.quantity, part.unit_cost, 
          part.where_to_buy, part.part_number, part.category))
    conn.commit()
    conn.close()
    return {"success": True}

# Instructions API
@app.post("/api/jobs/{job_id}/instructions")
async def add_job_instruction(job_id: int, instruction: Instruction):
    """Add an instruction step to a job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO instructions (job_id, step_number, instruction, safety_note, tools_needed, estimated_minutes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (job_id, instruction.step_number, instruction.instruction, instruction.safety_note,
          instruction.tools_needed, instruction.estimated_minutes))
    conn.commit()
    conn.close()
    return {"success": True}

# Maintenance Reminders API
@app.get("/api/reminders")
async def get_reminders():
    """Get all maintenance reminders"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM maintenance_reminders ORDER BY next_due ASC")
    reminders = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    return reminders

@app.post("/api/reminders")
async def create_reminder(reminder: MaintenanceReminder):
    """Create a new maintenance reminder"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate next due date
    next_due = datetime.now() + timedelta(days=reminder.frequency_days)
    
    cursor.execute("""
        INSERT INTO maintenance_reminders (title, description, frequency_days, next_due, category, priority, auto_schedule)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (reminder.title, reminder.description, reminder.frequency_days, next_due.date(),
          reminder.category, reminder.priority, reminder.auto_schedule))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/api/reminders/overdue")
async def get_overdue_reminders():
    """Get overdue maintenance reminders"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM maintenance_reminders 
        WHERE next_due <= date('now') 
        ORDER BY next_due ASC
    """)
    overdue = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    return overdue

# AI Chat API (simplified)
@app.post("/api/chat")
async def chat_with_fred(request: Request):
    """Chat with Fix-It Fred AI assistant"""
    data = await request.json()
    message = data.get("message", "")
    
    # This is a simplified response - in production, this would use a real AI service
    response = generate_fred_response(message)
    
    return {"response": response}

def generate_fred_response(message: str) -> str:
    """Generate AI response (simplified version)"""
    message_lower = message.lower()
    
    # Home maintenance responses
    if any(word in message_lower for word in ['furnace', 'filter', 'hvac', 'air']):
        return """For HVAC maintenance, here's what I recommend:

**Furnace Filter Changes:**
- Check monthly, replace every 1-3 months
- Common sizes: 16x20x1, 20x25x1, 16x25x1
- Cost: $5-15 per filter
- Location: Usually near furnace unit or return air vent

**Steps:**
1. Turn off HVAC system
2. Locate filter compartment
3. Note airflow direction arrow
4. Replace with new filter (same direction)
5. Turn system back on

Would you like me to set up a monthly reminder for this?"""

    elif any(word in message_lower for word in ['oil', 'change', 'car', 'vehicle']):
        return """Oil change intervals depend on your vehicle:

**Frequency:**
- Conventional oil: every 3,000-5,000 miles
- Synthetic blend: every 5,000-7,500 miles  
- Full synthetic: every 7,500-10,000 miles

**What you'll need:**
- Motor oil (check owner's manual for type/amount)
- Oil filter
- Drain plug gasket
- Basic tools: wrench set, oil filter wrench, drain pan

**Estimated cost:** $25-60 if DIY, $40-100 at shop

I can create a detailed job plan with step-by-step instructions if you'd like to do it yourself!"""

    elif any(word in message_lower for word in ['leak', 'faucet', 'drip', 'water']):
        return """Leaky faucets are usually easy to fix! Common causes:

**Most likely issues:**
- Worn washers or O-rings ($1-5 fix)
- Faulty cartridge ($10-25 fix)
- Loose packing nut (free fix)

**First steps:**
1. Turn off water supply under sink
2. Identify faucet type (single/double handle)
3. Take photos before disassembly

**Tools needed:**
- Adjustable wrench
- Screwdrivers
- Pliers

Would you like specific instructions for your faucet type? I can also create a parts list once you tell me the make/model."""

    elif any(word in message_lower for word in ['reminder', 'schedule', 'when']):
        return """I can set up maintenance reminders for any regular tasks! Here are some common ones:

**Monthly:**
- HVAC filter check
- Test smoke detectors
- Check tire pressure

**Quarterly:** 
- Vehicle oil change
- Deep clean appliances
- Inspect weatherstripping

**Seasonally:**
- Gutter cleaning
- HVAC system tune-up
- Exterior maintenance

**Annually:**
- Replace smoke detector batteries
- Service water heater
- Roof inspection

What specific reminders would you like me to set up? I can customize the frequency for your needs."""

    else:
        return """I'm Fix-It Fred, your DIY assistant! I can help with:

🔧 **Job Planning** - Step-by-step instructions for any repair
🛒 **Parts Lists** - What to buy and where to get it  
⏰ **Maintenance Reminders** - Never miss important tasks
🛠️ **Tool Guidance** - What tools you need for each job
💡 **Safety Tips** - Keep you safe during DIY projects

Common questions I help with:
- Home repairs (plumbing, electrical, HVAC)
- Vehicle maintenance  
- Seasonal home maintenance
- Emergency fixes
- Preventive maintenance scheduling

What project or maintenance task can I help you with today?"""

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    
    # Add sample data if database is empty
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM maintenance_reminders")
    if cursor.fetchone()[0] == 0:
        # Add sample reminders
        sample_reminders = [
            ("Change Furnace Filter", "Replace HVAC filter for better air quality", 30, "hvac", "high"),
            ("Vehicle Oil Change", "Change engine oil and filter", 90, "automotive", "high"),
            ("Test Smoke Detectors", "Test all smoke detector batteries", 30, "safety", "high"),
            ("Clean Gutters", "Remove debris and check drainage", 180, "exterior", "medium"),
            ("Service Water Heater", "Annual water heater maintenance", 365, "plumbing", "medium")
        ]
        
        for title, desc, freq, cat, priority in sample_reminders:
            next_due = datetime.now() + timedelta(days=freq)
            cursor.execute("""
                INSERT INTO maintenance_reminders (title, description, frequency_days, category, priority, next_due)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, desc, freq, cat, priority, next_due.date()))
        
        conn.commit()
    
    conn.close()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)