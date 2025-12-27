"""
Email service - SendGrid integration for transactional and bulk emails.
"""
from typing import List, Optional
from config import settings
import httpx
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """SendGrid email service wrapper."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@example.com')
        self.base_url = "https://api.sendgrid.com/v3"
    
    @property
    def is_configured(self) -> bool:
        """Check if SendGrid is properly configured."""
        return bool(self.api_key)
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> dict:
        """
        Send a single email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html: Optional HTML body
            from_email: Optional sender email (uses default if not provided)
            
        Returns:
            Response dict with status
        """
        if not self.is_configured:
            logger.warning("SendGrid not configured, email not sent")
            return {"status": "skipped", "message": "Email service not configured"}
        
        sender = from_email or self.from_email
        
        email_data = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": sender},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}]
        }
        
        if html:
            email_data["content"].append({"type": "text/html", "value": html})
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=email_data
                )
                
                if response.status_code in [200, 202]:
                    logger.info(f"Email sent to {to}")
                    return {"status": "success", "message": f"Email sent to {to}"}
                else:
                    logger.error(f"SendGrid error: {response.text}")
                    return {"status": "error", "message": response.text}
                    
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_bulk_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> dict:
        """
        Send email to multiple recipients.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html: Optional HTML body
            
        Returns:
            Response dict with status and count
        """
        if not self.is_configured:
            return {"status": "skipped", "message": "Email service not configured"}
        
        email_data = {
            "personalizations": [{"to": [{"email": email} for email in to]}],
            "from": {"email": self.from_email},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}]
        }
        
        if html:
            email_data["content"].append({"type": "text/html", "value": html})
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=email_data
                )
                
                if response.status_code in [200, 202]:
                    logger.info(f"Bulk email sent to {len(to)} recipients")
                    return {"status": "success", "count": len(to)}
                else:
                    return {"status": "error", "message": response.text}
                    
        except Exception as e:
            logger.error(f"Bulk email failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_password_reset(self, to: str, reset_token: str, reset_url: str) -> dict:
        """Send password reset email."""
        subject = "Password Reset Request"
        body = f"""
You have requested to reset your password.

Click the link below to reset your password:
{reset_url}?token={reset_token}

This link will expire in 1 hour.

If you did not request this, please ignore this email.
"""
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Password Reset Request</h2>
    <p>You have requested to reset your password.</p>
    <p>
        <a href="{reset_url}?token={reset_token}" 
           style="background-color: #007bff; color: white; padding: 10px 20px; 
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            Reset Password
        </a>
    </p>
    <p><small>This link will expire in 1 hour.</small></p>
    <p><small>If you did not request this, please ignore this email.</small></p>
</body>
</html>
"""
        return await self.send_email(to, subject, body, html)
    
    async def send_welcome(self, to: str, name: str) -> dict:
        """Send welcome email to new user."""
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        subject = "Welcome to Malaysian Legal AI"
        body = f"""
Dear {name},

Welcome to Malaysian Legal AI Agent System!

You can now access all features including:
- Document processing with OCR
- Bilingual legal drafting (Malay/English)
- Legal research and case analysis
- Evidence workflow management

Get started by logging in at: {frontend_url}

Best regards,
The Malaysian Legal AI Team
"""
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Welcome to Malaysian Legal AI!</h2>
    <p>Dear {name},</p>
    <p>Thank you for joining us! You now have access to:</p>
    <ul>
        <li>Document processing with OCR</li>
        <li>Bilingual legal drafting (Malay/English)</li>
        <li>Legal research and case analysis</li>
        <li>Evidence workflow management</li>
    </ul>
    <p>
        <a href="{frontend_url}" 
           style="background-color: #28a745; color: white; padding: 10px 20px; 
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            Get Started
        </a>
    </p>
    <p>Best regards,<br>The Malaysian Legal AI Team</p>
</body>
</html>
"""
        return await self.send_email(to, subject, body, html)


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


# Convenience functions
async def send_email(to: str, subject: str, body: str, html: Optional[str] = None) -> dict:
    """Send a single email (convenience function)."""
    service = get_email_service()
    return await service.send_email(to, subject, body, html)


async def send_bulk_email(to: List[str], subject: str, body: str, html: Optional[str] = None) -> dict:
    """Send bulk email (convenience function)."""
    service = get_email_service()
    return await service.send_bulk_email(to, subject, body, html)
