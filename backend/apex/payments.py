"""
Apex Payments Module - PayPal integration wrapper.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
import base64
import logging

logger = logging.getLogger(__name__)


class PayPalClient:
    """
    PayPal API client for payment processing.
    
    Supports:
    - Order creation and capture
    - Subscription management
    - Webhook handling
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        mode: str = "sandbox"  # sandbox or live
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.mode = mode
        
        if mode == "sandbox":
            self.base_url = "https://api-m.sandbox.paypal.com"
        else:
            self.base_url = "https://api-m.paypal.com"
        
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token from PayPal."""
        # Check if we have a valid cached token
        if self._access_token and self._token_expires:
            if datetime.utcnow() < self._token_expires:
                return self._access_token
        
        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal credentials not configured")
        
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"}
            )
            
            if response.status_code != 200:
                logger.error(f"PayPal token error: {response.text}")
                raise ValueError(f"Failed to get PayPal token: {response.status_code}")
            
            data = response.json()
            self._access_token = data["access_token"]
            # Token typically expires in 9 hours, we'll refresh after 8
            from datetime import timedelta
            self._token_expires = datetime.utcnow() + timedelta(hours=8)
            
            return self._access_token
    
    async def create_order(
        self,
        amount: float,
        currency: str = "USD",
        description: Optional[str] = None,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a PayPal order.
        
        Returns:
            Dict with order_id, status, and approval_url
        """
        token = await self._get_access_token()
        
        order_data: Dict[str, Any] = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": f"{amount:.2f}"
                }
            }]
        }
        
        if description:
            order_data["purchase_units"][0]["description"] = description
        
        if return_url and cancel_url:
            order_data["application_context"] = {
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=order_data
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"PayPal order error: {response.text}")
                raise ValueError(f"Failed to create order: {response.status_code}")
            
            data = response.json()
            
            # Extract approval URL
            approval_url = None
            for link in data.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            logger.info(f"PayPal order created: {data.get('id')}")
            
            return {
                "order_id": data.get("id"),
                "status": data.get("status"),
                "approval_url": approval_url,
                "raw_response": data
            }
    
    async def capture_order(self, order_id: str) -> Dict[str, Any]:
        """
        Capture a PayPal order after customer approval.
        
        Returns:
            Dict with capture details
        """
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"PayPal capture error: {response.text}")
                raise ValueError(f"Failed to capture order: {response.status_code}")
            
            data = response.json()
            logger.info(f"PayPal order captured: {order_id}")
            
            return {
                "order_id": data.get("id"),
                "status": data.get("status"),
                "payer": data.get("payer", {}),
                "raw_response": data
            }
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details."""
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/checkout/orders/{order_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get order: {response.status_code}")
            
            return response.json()
    
    async def create_subscription(
        self,
        plan_id: str,
        subscriber_email: str,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a PayPal subscription.
        
        Note: Requires a pre-configured plan in PayPal.
        """
        token = await self._get_access_token()
        
        subscription_data = {
            "plan_id": plan_id,
            "subscriber": {
                "email_address": subscriber_email
            }
        }
        
        if return_url and cancel_url:
            subscription_data["application_context"] = {
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/billing/subscriptions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=subscription_data
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"PayPal subscription error: {response.text}")
                raise ValueError(f"Failed to create subscription: {response.status_code}")
            
            data = response.json()
            
            # Extract approval URL
            approval_url = None
            for link in data.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            return {
                "subscription_id": data.get("id"),
                "status": data.get("status"),
                "approval_url": approval_url,
                "raw_response": data
            }
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, str]:
        """Cancel a PayPal subscription."""
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/cancel",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"reason": reason or "Cancelled by user"}
            )
            
            if response.status_code != 204:
                raise ValueError(f"Failed to cancel subscription: {response.status_code}")
            
            logger.info(f"PayPal subscription cancelled: {subscription_id}")
            
            return {"status": "cancelled", "subscription_id": subscription_id}


# Singleton client instance
_paypal_client: Optional[PayPalClient] = None


def init_payments(
    client_id: str,
    client_secret: str,
    mode: str = "sandbox"
) -> PayPalClient:
    """Initialize the PayPal client."""
    global _paypal_client
    _paypal_client = PayPalClient(client_id, client_secret, mode)
    return _paypal_client


def get_paypal_client() -> Optional[PayPalClient]:
    """Get the PayPal client instance."""
    return _paypal_client
