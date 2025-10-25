#!/usr/bin/env python3
"""
Budget Tracker for Grok/Fred - Keep costs low for broke users!
Tracks token usage and implements spending limits
"""

import json
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import sqlite3

app = FastAPI(title="Budget Tracker", version="1.0.0")

class TokenUsage(BaseModel):
    user_id: str = "default"
    tokens_used: int
    service: str  # "grok" or "fred"
    message: str
    response_tokens: int = 0

class BudgetSettings(BaseModel):
    daily_limit: int = 1000
    per_request_limit: int = 150
    warning_threshold: float = 0.7  # 70%
    critical_threshold: float = 0.9  # 90%

# Initialize database
def init_db():
    """Initialize SQLite database for budget tracking"""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            date TEXT,
            service TEXT,
            tokens_used INTEGER,
            message TEXT,
            timestamp TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budget_settings (
            user_id TEXT PRIMARY KEY,
            daily_limit INTEGER,
            per_request_limit INTEGER,
            warning_threshold REAL,
            critical_threshold REAL
        )
    ''')
    
    # Insert default settings
    cursor.execute('''
        INSERT OR IGNORE INTO budget_settings 
        (user_id, daily_limit, per_request_limit, warning_threshold, critical_threshold)
        VALUES (?, ?, ?, ?, ?)
    ''', ("default", 1000, 150, 0.7, 0.9))
    
    conn.commit()
    conn.close()

def get_today_usage(user_id: str = "default") -> Dict:
    """Get today's token usage for user"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT SUM(tokens_used), COUNT(*) 
        FROM token_usage 
        WHERE user_id = ? AND date = ?
    ''', (user_id, today))
    
    result = cursor.fetchone()
    tokens_used = result[0] if result[0] else 0
    request_count = result[1] if result[1] else 0
    
    # Get budget settings
    cursor.execute('''
        SELECT daily_limit, per_request_limit, warning_threshold, critical_threshold
        FROM budget_settings 
        WHERE user_id = ?
    ''', (user_id,))
    
    settings = cursor.fetchone()
    if not settings:
        settings = (1000, 150, 0.7, 0.9)  # Default values
    
    conn.close()
    
    daily_limit, per_request_limit, warning_threshold, critical_threshold = settings
    
    return {
        "tokens_used": tokens_used,
        "tokens_remaining": max(0, daily_limit - tokens_used),
        "daily_limit": daily_limit,
        "per_request_limit": per_request_limit,
        "request_count": request_count,
        "percentage_used": (tokens_used / daily_limit) * 100,
        "status": get_budget_status(tokens_used, daily_limit, warning_threshold, critical_threshold),
        "can_make_request": tokens_used < daily_limit
    }

def get_budget_status(tokens_used: int, daily_limit: int, warning_threshold: float, critical_threshold: float) -> str:
    """Get budget status based on usage"""
    percentage = tokens_used / daily_limit
    
    if percentage >= critical_threshold:
        return "critical"
    elif percentage >= warning_threshold:
        return "warning"
    else:
        return "normal"

def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation)"""
    # Very rough estimate: 1 token ≈ 4 characters
    return max(1, len(text) // 4)

def log_usage(user_id: str, service: str, tokens_used: int, message: str):
    """Log token usage to database"""
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().isoformat()
    
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO token_usage (user_id, date, service, tokens_used, message, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, today, service, tokens_used, message[:100], timestamp))
    
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

@app.get("/")
async def root():
    """Budget tracker status"""
    return {
        "service": "Budget Tracker",
        "status": "active",
        "purpose": "Keep AI costs low for broke users! 💸",
        "daily_limit": 1000,
        "tracking": "tokens per day"
    }

@app.get("/budget/{user_id}")
async def get_budget_status_endpoint(user_id: str = "default"):
    """Get current budget status for user"""
    return get_today_usage(user_id)

@app.post("/budget/check")
async def check_budget_before_request(usage: TokenUsage):
    """Check if user can make a request within budget"""
    current_usage = get_today_usage(usage.user_id)
    estimated_tokens = estimate_tokens(usage.message)
    
    if current_usage["tokens_used"] + estimated_tokens > current_usage["daily_limit"]:
        return {
            "can_proceed": False,
            "reason": "Daily token limit exceeded",
            "tokens_used": current_usage["tokens_used"],
            "daily_limit": current_usage["daily_limit"],
            "estimated_cost": estimated_tokens,
            "suggestion": "Try tomorrow or ask shorter questions"
        }
    
    if estimated_tokens > current_usage["per_request_limit"]:
        return {
            "can_proceed": False,
            "reason": "Single request too large",
            "estimated_cost": estimated_tokens,
            "limit": current_usage["per_request_limit"],
            "suggestion": "Make your question shorter and more specific"
        }
    
    return {
        "can_proceed": True,
        "estimated_cost": estimated_tokens,
        "remaining_budget": current_usage["tokens_remaining"],
        "percentage_used": current_usage["percentage_used"]
    }

@app.post("/budget/log")
async def log_token_usage(usage: TokenUsage):
    """Log actual token usage after API call"""
    total_tokens = usage.tokens_used + usage.response_tokens
    log_usage(usage.user_id, usage.service, total_tokens, usage.message)
    
    updated_usage = get_today_usage(usage.user_id)
    
    return {
        "logged": True,
        "tokens_charged": total_tokens,
        "updated_usage": updated_usage,
        "warning": get_budget_warning(updated_usage)
    }

def get_budget_warning(usage: Dict) -> Optional[str]:
    """Generate budget warning message"""
    status = usage["status"]
    percentage = usage["percentage_used"]
    
    if status == "critical":
        return f"🚨 BUDGET CRITICAL! {percentage:.1f}% used. Stop using AI or you'll go more broke!"
    elif status == "warning":
        return f"⚠️ Budget Warning: {percentage:.1f}% used. Slow down to avoid running out!"
    elif percentage > 50:
        return f"💸 {percentage:.1f}% budget used. Be careful with spending!"
    else:
        return None

@app.get("/budget/stats/{user_id}")
async def get_usage_stats(user_id: str = "default"):
    """Get detailed usage statistics"""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    # Get last 7 days
    days_data = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT SUM(tokens_used), COUNT(*), service
            FROM token_usage 
            WHERE user_id = ? AND date = ?
            GROUP BY service
        ''', (user_id, date))
        
        day_usage = {"date": date, "fred": 0, "grok": 0, "total": 0}
        for row in cursor.fetchall():
            tokens, count, service = row
            day_usage[service] = tokens
            day_usage["total"] += tokens
        
        days_data.append(day_usage)
    
    conn.close()
    
    return {
        "user_id": user_id,
        "last_7_days": days_data,
        "current_status": get_today_usage(user_id)
    }

@app.post("/budget/settings/{user_id}")
async def update_budget_settings(user_id: str, settings: BudgetSettings):
    """Update budget settings for user"""
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO budget_settings 
        (user_id, daily_limit, per_request_limit, warning_threshold, critical_threshold)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, settings.daily_limit, settings.per_request_limit, 
          settings.warning_threshold, settings.critical_threshold))
    
    conn.commit()
    conn.close()
    
    return {
        "updated": True,
        "user_id": user_id,
        "new_settings": settings.dict()
    }

@app.get("/budget/emergency-stop/{user_id}")
async def emergency_budget_stop(user_id: str = "default"):
    """Emergency stop - set daily limit to current usage"""
    current_usage = get_today_usage(user_id)
    
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE budget_settings 
        SET daily_limit = ?
        WHERE user_id = ?
    ''', (current_usage["tokens_used"], user_id))
    
    conn.commit()
    conn.close()
    
    return {
        "emergency_stop": True,
        "message": "🚨 Budget frozen at current usage to prevent overspending!",
        "frozen_at": current_usage["tokens_used"],
        "advice": "Reset tomorrow or increase limit if needed"
    }

if __name__ == "__main__":
    import uvicorn
    print("💸 Budget Tracker Starting...")
    print("🔒 Protecting broke users from AI overspending!")
    uvicorn.run(app, host="0.0.0.0", port=8009)