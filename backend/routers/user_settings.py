"""
User settings and preferences API - Lexis Cookie Management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_sync_db
from dependencies import get_current_user
from models.lexis_credentials import LexisCredentials
from services.lexis_scraper import LexisScraper
import logging

router = APIRouter(tags=["user_settings"])
logger = logging.getLogger(__name__)


# No wrapper needed for direct list input
# type LexisCookieRequest = List[dict]


class LexisCookieResponse(BaseModel):
    success: bool
    message: str
    auth_method: str
    expires_at: Optional[str] = None


@router.post("/lexis-cookies/validate")
async def validate_lexis_cookies(
    cookies: List[dict],
    current_user: dict = Depends(get_current_user)
):
    """
    Validate Lexis cookies without saving.
    Frontend calls this before showing "Save" option.
    """
    logger.info(f"🔍 Validating {len(cookies)} cookies for user {current_user.get('user_id')}")
    
    try:
        scraper = LexisScraper(use_pool=False)  # Use dedicated instance for validation
        await scraper.start_robot()
        
        try:
            logger.info("Injecting cookies into browser context...")
            await scraper.inject_cookies(cookies)
            
            logger.info("Navigating to Lexis Advance...")
            await scraper._page.goto("https://advance.lexis.com/search", timeout=30000, wait_until="domcontentloaded")
            
            logger.info("Checking login status...")
            valid = await scraper.check_is_logged_in()
            
            logger.info(f"Validation result: {valid}")
        finally:
            await scraper.close_robot()
        
        if valid:
            return {
                "valid": True,
                "message": "Cookies are valid and authenticated",
                "estimated_expiry": "24 hours"
            }
        else:
            return {
                "valid": False,
                "message": "Cookies are invalid or expired. Please ensure you're logged into Lexis Advance in your browser and export fresh cookies."
            }
    
    except Exception as e:
        logger.error(f"Cookie validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@router.post("/lexis-cookies/save", response_model=LexisCookieResponse)
async def save_lexis_cookies(
    cookies: List[dict],
    db: Session = Depends(get_sync_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Save validated Lexis cookies to user profile (encrypted).
    """
    try:
        # First validate
        scraper = LexisScraper(use_pool=False)
        await scraper.start_robot()
        
        try:
            await scraper.inject_cookies(cookies)
            await scraper._page.goto("https://advance.lexis.com/search", timeout=20000)
            valid = await scraper.check_is_logged_in()
        finally:
            await scraper.close_robot()
        
        if not valid:
            raise HTTPException(status_code=400, detail="Cookies are invalid or expired")
        
        # Get or create credentials record
        user_id = current_user["user_id"]
        creds = db.query(LexisCredentials).filter(LexisCredentials.user_id == user_id).first()
        
        if not creds:
            creds = LexisCredentials(user_id=user_id)
            db.add(creds)
        
        expiry = datetime.utcnow() + timedelta(hours=23)  # Conservative 23h expiry
        creds.set_cookies(cookies, expiry)
        db.commit()
        
        logger.info(f"✅ Saved Lexis cookies for user {user_id}")
        
        return LexisCookieResponse(
            success=True,
            message="Cookies saved successfully",
            auth_method="cookies",
            expires_at=expiry.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save cookies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lexis-cookies/status")
async def get_lexis_cookie_status(
    db: Session = Depends(get_sync_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current authentication method and cookie status."""
    user_id = current_user["user_id"]
    creds = db.query(LexisCredentials).filter(LexisCredentials.user_id == user_id).first()
    
    if not creds or not creds.cookies_encrypted:
        return {
            "auth_method": "um_library",
            "has_cookies": False,
            "status": "using_default"
        }
    
    if creds.auth_method == "cookies" and creds.cookies_expires_at:
        is_expired = datetime.utcnow() > creds.cookies_expires_at
        return {
            "auth_method": "cookies",
            "has_cookies": True,
            "expires_at": creds.cookies_expires_at.isoformat(),
            "is_expired": is_expired,
            "status": "expired" if is_expired else "active"
        }
    
    return {
        "auth_method": "um_library",
        "has_cookies": False,
        "status": "using_default"
    }


@router.delete("/lexis-cookies")
async def clear_lexis_cookies(
    db: Session = Depends(get_sync_db),
    current_user: dict = Depends(get_current_user)
):
    """Clear saved cookies and revert to UM Library authentication."""
    user_id = current_user["user_id"]
    creds = db.query(LexisCredentials).filter(LexisCredentials.user_id == user_id).first()
    
    if not creds:
        return {"success": True, "message": "No cookies to clear"}
    
    creds.clear_cookies()
    db.commit()
    
    logger.info(f"🗑️ Cleared Lexis cookies for user {user_id}")
    
    return {"success": True, "message": "Cookies cleared. Using UM Library authentication."}
