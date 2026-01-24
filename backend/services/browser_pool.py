"""
Browser Pool Service - Persistent Browser Connection for Performance.

This module provides a singleton browser pool that keeps Playwright browser
instances alive between searches, avoiding the 5-10 second startup penalty.

Features:
- Singleton pattern for browser reuse
- Session persistence with cookies
- Automatic reconnection on failure
- Thread-safe async operations
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from config import settings


logger = logging.getLogger(__name__)


class BrowserPool:
    """
    Singleton browser pool for Playwright.
    
    Keeps browser alive between requests to avoid cold start penalty.
    Automatically manages session cookies for Lexis authentication.
    """
    
    _instance: Optional['BrowserPool'] = None
    _lock = asyncio.Lock()
    
    # Persistent persistent page
    _persistent_page: Optional[Page] = None
    
    # Configuration
    BROWSER_TIMEOUT = timedelta(minutes=60)  # Keep browser open longer (1 hour)
    SESSION_CHECK_INTERVAL = timedelta(minutes=5)
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize attributes safely
            cls._instance._playwright = None
            cls._instance._browser = None
            cls._instance._context = None
            cls._instance._session_file = Path("lexis_session.json")
            cls._instance._last_used = None
        return cls._instance

    
    @classmethod
    async def get_instance(cls) -> 'BrowserPool':
        """Get or create the singleton instance."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    async def get_browser(self) -> Browser:
        """
        Public: Get or create a browser instance (Thread-safe).
        """
        async with self._lock:
            return await self._get_browser()

    async def _get_browser(self) -> Browser:
        """
        Internal: Get or create a browser instance.
        Assumes self._lock is already held.
        """
        if self._browser is None or not self._browser.is_connected():
            logger.info("🚀 Launching new browser instance (HEADED)...")
            
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            
            self._browser = await self._playwright.chromium.launch(
                headless=settings.LEXIS_HEADLESS,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu',
                    '--start-maximized'
                ]
            )
            logger.info("✅ Browser launched successfully")
        else:
            logger.info("♻️ Reusing existing browser instance")
        
        self._last_used = datetime.now()
        return self._browser


    async def _get_context(self) -> BrowserContext:
        """
        Internal: Get or create browser context with session support.
        Assumes self._lock is already held.
        """
        # Return existing if valid
        if self._context:
            try:
                # Quick check if open? Playwright doesn't have is_connected on context easily
                # But we can check if browser is connected
                if self._browser and self._browser.is_connected():
                        return self._context
            except:
                pass
            self._context = None

        logger.info("Creating new browser context...")
        browser = await self._get_browser()
        
        # Load session if exists

        storage_state = None
        if self._session_file.exists():
            try:
                with open(self._session_file, 'r') as f:
                    storage_state = json.load(f)
                logger.info("📂 Loaded session cookies from file")
            except Exception as e:
                logger.warning(f"Failed to load session: {e}")
        
        try:
            self._context = await browser.new_context(
                storage_state=storage_state,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )
        except Exception as e:
            logger.warning(f"Context creation failed (likely bad storage_state): {e}")
            # Retry without storage state
            self._context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )
            
        return self._context



    async def get_page(self) -> Page:
        """
        Get the persistent page instance.
        
        Refurbishes existing page if open, or creates new one.
        """
        async with self._lock:
            # Check if we have a valid persistent page
            if (self._persistent_page and 
                not self._persistent_page.is_closed() and 
                self._context):
                
                logger.info("♻️ Reusing PERSISENT page")
                self._last_used = datetime.now()
                return self._persistent_page
                
            logger.info("📄 Creating NEW persistent page...")
            context = await self._get_context()
            
            # Create new page

            page = await context.new_page()
            
            # Hide webdriver property to avoid bot detection
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            self._persistent_page = page
            return page

    async def release_page(self, page: Page):
        """
        Release page back to pool.
        
        For persistent strategy, we DO NOT close it.
        We just update the timestamp.
        """
        self._last_used = datetime.now()
        # Do not close!
    
    async def save_session(self, page: Page) -> bool:
        """
        Save current session cookies for future use.
        
        Should be called after successful Lexis login.
        """
        try:
            # Verify we're on Lexis domain before saving
            current_url = page.url
            lexis_domains = ["advance.lexis.com", "lexis.com.my", "lexismalaysia"]
            
            if not any(domain in current_url for domain in lexis_domains):
                logger.warning(f"⚠️ Not saving session - not on Lexis domain: {current_url}")
                return False
            
            if self._context:
                storage = await self._context.storage_state()
                with open(self._session_file, 'w') as f:
                    json.dump(storage, f)
                logger.info("💾 Session cookies saved successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
        return False
    
    async def invalidate_session(self):
        """
        Invalidate current session (force re-login on next request).
        """
        async with self._lock:
            if self._session_file.exists():
                self._session_file.unlink()
                logger.info("🗑️ Session file deleted")
            
            if self._context:
                try:
                    await self._context.close()
                except:
                    pass
                self._context = None
                logger.info("🗑️ Browser context cleared")
    
    async def close(self):
        """
        Close all browser resources.
        
        Call this on application shutdown.
        """
        async with self._lock:
            if self._context:
                try:
                    await self._context.close()
                except:
                    pass
                self._context = None
            
            if self._browser:
                try:
                    await self._browser.close()
                except:
                    pass
                self._browser = None
            
            if self._playwright:
                try:
                    await self._playwright.stop()
                except:
                    pass
                self._playwright = None
            
            logger.info("🛑 Browser pool closed")
    
    def _is_session_expired(self) -> bool:
        """Check if current session has expired based on last use time."""
        if self._last_used is None:
            return True
        return datetime.now() - self._last_used > self.BROWSER_TIMEOUT
    
    @classmethod
    async def health_check(cls) -> dict:
        """
        Get health status of the browser pool.
        
        Useful for monitoring and debugging.
        """
        instance = await cls.get_instance()
        return {
            "browser_connected": instance._browser is not None and instance._browser.is_connected(),
            "context_active": instance._context is not None,
            "session_file_exists": instance._session_file.exists(),
            "last_used": instance._last_used.isoformat() if instance._last_used else None,
            "idle_minutes": (datetime.now() - instance._last_used).total_seconds() / 60 if instance._last_used else None
        }


# Convenience function for getting a page
async def get_pooled_page() -> Page:
    """
    Convenience function to get a page from the browser pool.
    
    Usage:
        page = await get_pooled_page()
        try:
            await page.goto("https://example.com")
            # ... do stuff
        finally:
            await page.close()
    """
    pool = await BrowserPool.get_instance()
    return await pool.get_page()


# Cleanup function for application shutdown
async def cleanup_browser_pool():
    """
    Cleanup browser pool on application shutdown.
    
    Call this in FastAPI's shutdown event.
    """
    pool = await BrowserPool.get_instance()
    await pool.close()
