"""
Basic Email Service for ChatterFix
Simple SMTP email sending for notifications
"""

import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EmailService:
    """Simple email service using SMTP"""
    
    def __init__(self):
        # Email configuration from environment
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@chatterfix.com")
        self.from_name = os.getenv("FROM_NAME", "ChatterFix CMMS")
        
        # Check if email is configured
        self.email_configured = bool(self.smtp_username and self.smtp_password)
        
        if not self.email_configured:
            logger.warning("Email not configured - using logging fallback")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str = None,
        to_name: str = None
    ) -> bool:
        """Send an email"""
        try:
            if not self.email_configured:
                # Fallback to logging
                logger.info(f"EMAIL TO: {to_email}")
                logger.info(f"EMAIL SUBJECT: {subject}")
                logger.info(f"EMAIL BODY:\n{body_text}")
                return True
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
            
            # Add text part
            text_part = MIMEText(body_text, "plain")
            msg.attach(text_part)
            
            # Add HTML part if provided
            if body_html:
                html_part = MIMEText(body_html, "html")
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_welcome_email(self, user_data: Dict[str, Any], password: str) -> bool:
        """Send welcome email to new user"""
        subject = "Welcome to ChatterFix CMMS!"
        
        body_text = f"""
Welcome to ChatterFix CMMS, {user_data.get('fullName', 'New User')}!

Your account has been created successfully:

Email: {user_data.get('email')}
Password: {password}

Please log in and change your password as soon as possible.

Best regards,
The ChatterFix Team
"""
        
        body_html = f"""
<html>
<body>
<h2>Welcome to ChatterFix CMMS!</h2>

<p>Hello {user_data.get('fullName', 'New User')},</p>

<p>Your account has been created successfully:</p>

<ul>
<li><strong>Email:</strong> {user_data.get('email')}</li>
<li><strong>Password:</strong> {password}</li>
</ul>

<p>Please log in and change your password as soon as possible.</p>

<p>Best regards,<br>The ChatterFix Team</p>
</body>
</html>
"""
        
        return await self.send_email(
            to_email=user_data.get('email'),
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            to_name=user_data.get('fullName')
        )

    async def send_password_reset_email(self, user_data: Dict[str, Any], password: str) -> bool:
        """Send password reset email"""
        subject = "Your ChatterFix CMMS Password"
        
        body_text = f"""
Hello {user_data.get('fullName', 'User')},

Here are your ChatterFix CMMS login credentials:

Email: {user_data.get('email')}
Password: {password}

Please log in and change your password as soon as possible.

Best regards,
The ChatterFix Team
"""
        
        return await self.send_email(
            to_email=user_data.get('email'),
            subject=subject,
            body_text=body_text,
            to_name=user_data.get('fullName')
        )

    async def send_work_order_notification(
        self, 
        to_email: str, 
        to_name: str, 
        work_order: Dict[str, Any],
        notification_type: str = "assigned"
    ) -> bool:
        """Send work order notification email"""
        try:
            wo_id = work_order.get('id', 'N/A')
            wo_title = work_order.get('title', 'Work Order')
            wo_description = work_order.get('description', 'No description')
            wo_priority = work_order.get('priority', 'normal').title()
            asset_name = work_order.get('asset_name', 'Unknown Asset')
            
            if notification_type == "assigned":
                subject = f"Work Order Assigned: {wo_title} (#{wo_id})"
                action_text = "has been assigned to you"
                action_html = "<strong>has been assigned to you</strong>"
            elif notification_type == "completed":
                subject = f"Work Order Completed: {wo_title} (#{wo_id})"
                action_text = "has been completed"
                action_html = "<strong>has been completed</strong>"
            elif notification_type == "updated":
                subject = f"Work Order Updated: {wo_title} (#{wo_id})"
                action_text = "has been updated"
                action_html = "<strong>has been updated</strong>"
            else:
                subject = f"Work Order Notification: {wo_title} (#{wo_id})"
                action_text = "requires your attention"
                action_html = "<strong>requires your attention</strong>"

            body_text = f"""
Hello {to_name},

Work Order #{wo_id} {action_text}:

Title: {wo_title}
Asset: {asset_name}
Priority: {wo_priority}
Description: {wo_description}

Please log in to ChatterFix CMMS to view the full details and take appropriate action.

Best regards,
ChatterFix CMMS System
"""

            body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
    <h2 style="color: #2c3e50;">Work Order Notification</h2>
    
    <p>Hello <strong>{to_name}</strong>,</p>
    
    <p>Work Order <strong>#{wo_id}</strong> {action_html}:</p>
    
    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #495057;">{wo_title}</h3>
        <p><strong>Asset:</strong> {asset_name}</p>
        <p><strong>Priority:</strong> <span style="color: {'#e74c3c' if wo_priority.lower() == 'urgent' else '#f39c12' if wo_priority.lower() == 'high' else '#27ae60'};">{wo_priority}</span></p>
        <p><strong>Description:</strong> {wo_description}</p>
    </div>
    
    <p>Please log in to ChatterFix CMMS to view the full details and take appropriate action.</p>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
        <p>Best regards,<br>ChatterFix CMMS System</p>
    </div>
</div>
</body>
</html>
"""

            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                to_name=to_name
            )
        except Exception as e:
            logger.error(f"Failed to send work order notification: {e}")
            return False

    async def send_training_notification(
        self, 
        to_email: str, 
        to_name: str, 
        training_title: str,
        training_id: str = None,
        notification_type: str = "assigned"
    ) -> bool:
        """Send training notification email"""
        try:
            if notification_type == "assigned":
                subject = f"Training Assigned: {training_title}"
                action_text = "has been assigned to you"
                action_html = "<strong>has been assigned to you</strong>"
            elif notification_type == "due":
                subject = f"Training Due: {training_title}"
                action_text = "is due for completion"
                action_html = "<strong>is due for completion</strong>"
            elif notification_type == "completed":
                subject = f"Training Completed: {training_title}"
                action_text = "has been completed"
                action_html = "<strong>has been completed</strong>"
            else:
                subject = f"Training Notification: {training_title}"
                action_text = "requires your attention"
                action_html = "<strong>requires your attention</strong>"

            body_text = f"""
Hello {to_name},

The training module "{training_title}" {action_text}.

Please log in to ChatterFix CMMS Training Center to access your training materials and complete the required coursework.

Training Link: /training/modules/{training_id or 'pending'}

Best regards,
ChatterFix CMMS Training System
"""

            body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
    <h2 style="color: #2c3e50;">Training Notification</h2>
    
    <p>Hello <strong>{to_name}</strong>,</p>
    
    <p>The training module <strong>"{training_title}"</strong> {action_html}.</p>
    
    <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #27ae60;">
        <h3 style="margin-top: 0; color: #27ae60;">📚 Training Module</h3>
        <p style="font-size: 16px; margin: 0;"><strong>{training_title}</strong></p>
    </div>
    
    <p>Please log in to ChatterFix CMMS Training Center to access your training materials and complete the required coursework.</p>
    
    <div style="text-align: center; margin: 25px 0;">
        <a href="/training/modules/{training_id or 'pending'}" style="background: #27ae60; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">Access Training</a>
    </div>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
        <p>Best regards,<br>ChatterFix CMMS Training System</p>
    </div>
</div>
</body>
</html>
"""

            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                to_name=to_name
            )
        except Exception as e:
            logger.error(f"Failed to send training notification: {e}")
            return False

    async def send_parts_notification(
        self, 
        to_email: str, 
        to_name: str, 
        parts_info: Dict[str, Any],
        notification_type: str = "arrived"
    ) -> bool:
        """Send parts/inventory notification email"""
        try:
            part_name = parts_info.get('name', 'Parts')
            part_number = parts_info.get('part_number', 'N/A')
            quantity = parts_info.get('quantity', 'N/A')
            location = parts_info.get('location', 'Unknown')

            if notification_type == "arrived":
                subject = f"Parts Arrived: {part_name} ({part_number})"
                action_text = "have arrived"
                action_html = "<strong style='color: #27ae60;'>have arrived</strong>"
            elif notification_type == "low_stock":
                subject = f"Low Stock Alert: {part_name} ({part_number})"
                action_text = "are running low"
                action_html = "<strong style='color: #e74c3c;'>are running low</strong>"
            else:
                subject = f"Parts Notification: {part_name}"
                action_text = "require attention"
                action_html = "<strong>require attention</strong>"

            body_text = f"""
Hello {to_name},

Parts notification for {part_name} (Part #{part_number}):

The following parts {action_text}:
- Part Name: {part_name}
- Part Number: {part_number}
- Quantity: {quantity}
- Location: {location}

Please check the inventory system for more details.

Best regards,
ChatterFix CMMS Inventory System
"""

            body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
    <h2 style="color: #2c3e50;">Parts Notification</h2>
    
    <p>Hello <strong>{to_name}</strong>,</p>
    
    <p>Parts notification for <strong>{part_name}</strong> (Part #{part_number}):</p>
    
    <p>The following parts {action_html}:</p>
    
    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <ul style="margin: 0; padding-left: 20px;">
            <li><strong>Part Name:</strong> {part_name}</li>
            <li><strong>Part Number:</strong> {part_number}</li>
            <li><strong>Quantity:</strong> {quantity}</li>
            <li><strong>Location:</strong> {location}</li>
        </ul>
    </div>
    
    <p>Please check the inventory system for more details.</p>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
        <p>Best regards,<br>ChatterFix CMMS Inventory System</p>
    </div>
</div>
</body>
</html>
"""

            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                to_name=to_name
            )
        except Exception as e:
            logger.error(f"Failed to send parts notification: {e}")
            return False


# Global email service instance
email_service = EmailService()