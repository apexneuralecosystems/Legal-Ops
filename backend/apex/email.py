"""
Apex Email Module - SendGrid integration for transactional emails.
"""
from typing import Optional
import logging
import httpx

logger = logging.getLogger(__name__)


class EmailClient:
    """
    SendGrid email client for sending transactional emails.
    
    Supports:
    - Password reset emails
    - Subscription confirmation emails
    - Payment receipt emails
    """
    
    def __init__(self, api_key: str, from_email: str):
        self.api_key = api_key
        self.from_email = from_email
        self.base_url = "https://api.sendgrid.com/v3"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SendGrid.
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.api_key:
            logger.warning("SendGrid API key not configured - skipping email")
            return False
        
        payload = {
            "personalizations": [
                {"to": [{"email": to_email}]}
            ],
            "from": {"email": self.from_email},
            "subject": subject,
            "content": [
                {"type": "text/html", "value": html_content}
            ]
        }
        
        if text_content:
            payload["content"].insert(0, {"type": "text/plain", "value": text_content})
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Email sent successfully to {to_email}")
                    return True
                else:
                    logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url_base: str
    ) -> bool:
        """Send password reset email with reset link."""
        reset_link = f"{reset_url_base}?token={reset_token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">Legal-Ops</h1>
            </div>
            <div style="padding: 40px 20px; background: #f9f9f9;">
                <h2 style="color: #333;">Password Reset Request</h2>
                <p style="color: #666; line-height: 1.6;">
                    We received a request to reset your password. Click the button below to create a new password:
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 40px; 
                              text-decoration: none; 
                              border-radius: 8px;
                              font-weight: bold;
                              display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #999; font-size: 12px;">
                    This link expires in 1 hour. If you didn't request this, please ignore this email.
                </p>
            </div>
            <div style="padding: 20px; text-align: center; background: #333; color: #999; font-size: 12px;">
                © 2024 Legal-Ops Hub. All rights reserved.
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        We received a request to reset your password.
        
        Click this link to reset your password:
        {reset_link}
        
        This link expires in 1 hour.
        
        If you didn't request this, please ignore this email.
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Reset Your Legal-Ops Password",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_subscription_confirmation(
        self,
        to_email: str,
        subscription_id: str
    ) -> bool:
        """Send subscription confirmation email."""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">🎉 Welcome to Pro!</h1>
            </div>
            <div style="padding: 40px 20px; background: #f9f9f9;">
                <h2 style="color: #333;">Your subscription is now active!</h2>
                <p style="color: #666; line-height: 1.6;">
                    Thank you for subscribing to Legal-Ops Pro. You now have unlimited access to all workflows:
                </p>
                <ul style="color: #666; line-height: 2;">
                    <li>✅ Unlimited Intake Processing</li>
                    <li>✅ Unlimited Document Drafting</li>
                    <li>✅ Unlimited Legal Research</li>
                    <li>✅ Unlimited Evidence Building</li>
                </ul>
                <p style="color: #999; font-size: 12px;">
                    Subscription ID: {subscription_id}
                </p>
            </div>
            <div style="padding: 20px; text-align: center; background: #333; color: #999; font-size: 12px;">
                © 2024 Legal-Ops Hub. All rights reserved.
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Welcome to Legal-Ops Pro! 🎉",
            html_content=html_content
        )


# Singleton instance
_email_client: Optional[EmailClient] = None


def init_email(api_key: str, from_email: str) -> EmailClient:
    """Initialize the email client."""
    global _email_client
    _email_client = EmailClient(api_key, from_email)
    logger.info(f"Email client initialized (from: {from_email})")
    return _email_client


def get_email_client() -> Optional[EmailClient]:
    """Get the email client instance."""
    return _email_client
