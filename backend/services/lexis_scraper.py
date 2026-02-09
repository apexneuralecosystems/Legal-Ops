"""
Lexis Advance Malaysia Scraper using Playwright ("Robot Browser").

AUTHENTICATION FLOW (CRITICAL):
1. Navigate to UM Library Database Portal (https://umlibguides.um.edu.my/az/databases?a=l)
2. DOM click on "Lexis Advance® Malaysia" link
3. Allow redirect: Library → EzProxy → CAS (with service= parameter)
4. Fill credentials on CAS page
5. Wait for redirect: CAS → EzProxy → Lexis Advance
6. Verify Lexis dashboard is loaded

NEVER navigate directly to CAS - the service= parameter MUST come from EzProxy.
"""
import os
import re
import json
import logging
import asyncio
import sys
from typing import List, Dict, Optional, Any
from datetime import datetime
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.async_api import Browser, Page, BrowserContext, TimeoutError
    from sqlalchemy.orm import Session
else:
    Browser = Any = object
    Page = Any = object
    BrowserContext = Any = object
    TimeoutError = Any = object
    Session = Any = object
from config import settings
from services.browser_pool import BrowserPool

# CRITICAL: Set Windows event loop policy BEFORE any Playwright usage
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LexisScraper:
    """
    Automated scraper for Lexis Advance Malaysia using Playwright Robot.
    
    Features:
    - Headless Browser Automation (Chrome)
    - Session Reuse (Cookies) for speed
    - Automatic University Auth (UM Login via EzProxy)
    - Jurisdiction Filtering
    - Strict Real Data (No Mock)
    """
    
    # Configuration - CORRECT ENTRY POINT (Not direct CAS!)
    UM_LIBRARY_PORTAL_URL = "https://umlibguides.um.edu.my/az/databases?a=l"
    
    # Expected domains for validation
    LEXIS_DOMAINS = ["advance.lexis.com", "lexis.com.my", "lexismalaysia"]
    EZPROXY_DOMAIN = "ezproxy.um.edu.my"
    CAS_DOMAIN = "sso-umlib.um.edu.my"
    
    # Required cookies for cookie-based authentication
    REQUIRED_COOKIE_NAMES = [
        "LexisAdvance_SessionId",
        "LexisAdvance_UserInfo",
        "LexisNexis.Preferences",
        "ASP.NET_SessionId"
    ]
    
    def __init__(self, use_pool: bool = False, db_session: Optional['Session'] = None):  # DISABLED pool by default for stability
        """Initialize settings from environment."""
        self.username = settings.LEXIS_USERNAME
        self.password = settings.LEXIS_PASSWORD
        self.headless = getattr(settings, "LEXIS_HEADLESS", True)
        self.timeout = 900000  # 15 minutes (extended for Option 3: fetching ALL judgments during search)
        self.use_pool = use_pool  # Browser pool disabled for connection stability
        self.db_session = db_session  # Database session for caching
        
        # Session storage
        self.session_file = Path("lexis_session.json")
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._pool: Optional[BrowserPool] = None
        
        # Cache service (Phase 3: Caching & Optimization)
        # TODO: JudgmentCacheService needs async conversion to work with AsyncSession
        # Temporarily disabled to prevent 'AsyncSession has no attribute query' errors
        self._cache_service = None
        # if db_session:
        #     from services.judgment_cache_service import JudgmentCacheService
        #     self._cache_service = JudgmentCacheService(db_session)
        #     logger.info("✨ Judgment caching ENABLED")
        
        # Debug captures directory
        self.debug_dir = Path("debug_captures")
        
        if not self.username or not self.password:
             logger.warning("LEXIS_USERNAME or LEXIS_PASSWORD not set. Login will fail.")

    async def start_robot(self):
        """Wake up the robot (Launch browser or get from pool)."""
        if self.use_pool:
            # Use browser pool for performance (saves 5-10 seconds per search)
            logger.info("🚀 Getting browser from pool...")
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    self._pool = await BrowserPool.get_instance()
                    self._page = await self._pool.get_page()
                    self._context = self._page.context  # Get context from pooled page
                    
                    # Verify the page is actually alive with a quick check
                    try:
                        _ = self._page.url
                        if self._page.is_closed():
                            raise Exception("Page is closed")
                    except Exception as health_err:
                        logger.warning(f"⚠️ Pooled page failed health check: {health_err}")
                        # Force pool to reset and retry
                        self._pool._persistent_page = None
                        self._pool._context = None
                        self._pool._browser = None
                        if attempt < max_retries - 1:
                            logger.info(f"🔄 Retrying pool (attempt {attempt + 2}/{max_retries})...")
                            continue
                        else:
                            raise Exception(f"Pool page dead after {max_retries} attempts")
                    
                    logger.info("✅ Got pooled browser page with context")
                    return
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Pool attempt {attempt + 1} failed: {e}, retrying...")
                        continue
                    logger.warning(f"⚠️ Pool failed after {max_retries} attempts: {e}, falling back to new browser")
                    self.use_pool = False  # Disable pool for this instance
        
        # Legacy: Launch new browser each time
        logger.info(f"🤖 Starting Robot Browser (Headless: {self.headless})...")
        from playwright.async_api import async_playwright
        p = await async_playwright().start()
        
        # Launch with stealth settings and stability improvements
        self._browser = await p.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--single-process',  # More stable for some systems
            ],
            timeout=60000  # Increase launch timeout
        )
        
        # Load session if exists for speed
        if self.session_file.exists():
            logger.info("Loading saved session cookies...")
            try:
                with open(self.session_file, 'r') as f:
                    storage_state = json.load(f)
                self._context = await self._browser.new_context(
                    storage_state=storage_state, 
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US'
                )
            except Exception as e:
                logger.warning(f"Could not load session: {e}. Starting fresh.")
                self._context = await self._browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US'
                )
        else:
            self._context = await self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )
        
        # Set default timeout on context to keep it alive during long fetching sessions
        self._context.set_default_timeout(self.timeout)  # 15 minutes
        self._context.set_default_navigation_timeout(self.timeout)  # 15 minutes for navigation
        
        self._page = await self._context.new_page()
        
        # Set page-level timeout as well
        self._page.set_default_timeout(self.timeout)  # 15 minutes
        self._page.set_default_navigation_timeout(self.timeout)  # 15 minutes for page navigation
        
        logger.info(f"✅ Browser timeouts set to {self.timeout/60000:.1f} minutes (keeps cookies alive during long fetches)")
        
        # Hide webdriver property to avoid bot detection
        await self._page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
    
    async def inject_cookies(self, cookies: List[Dict[str, Any]]):
        """
        Inject cookies into the browser context for cookie-based authentication.
        
        Args:
            cookies: List of cookie dictionaries from frontend
                Each cookie should have: name, value, domain, path, expires, httpOnly, secure
        
        Raises:
            ValueError: If required cookies are missing
        """
        if not self._context:
            error_msg = "Browser context not ready. Call start_robot() first."
            logger.error(f"❌ {error_msg}")
            logger.error(f"   Browser: {self._browser is not None}, Context: {self._context is not None}, Page: {self._page is not None}")
            raise RuntimeError(error_msg)
        
        # Validate required cookies are present
        cookie_names = {c.get("name") for c in cookies}
        missing = set(self.REQUIRED_COOKIE_NAMES) - cookie_names
        if missing:
            logger.warning(f"⚠️ Missing recommended cookies: {missing}")
        
        # Normalize cookie format for Playwright
        normalized_cookies = []
        for cookie in cookies:
            # Handle sameSite - convert browser export format to Playwright format
            same_site = cookie.get("sameSite")
            if same_site is None or same_site == "null" or same_site == "no_restriction":
                same_site = "None"  # Playwright expects "None" not null
            elif same_site not in ["Strict", "Lax", "None"]:
                same_site = "Lax"  # Default to Lax for safety
            
            # Handle expires - convert expirationDate to expires if needed
            expires = cookie.get("expires", cookie.get("expirationDate", -1))
            if expires == -1 or cookie.get("session", False):
                expires = -1  # Session cookie
            
            normalized = {
                "name": cookie.get("name"),
                "value": cookie.get("value", ""),
                "domain": cookie.get("domain", ".lexis.com"),
                "path": cookie.get("path", "/"),
                "expires": expires,
                "httpOnly": cookie.get("httpOnly", False),
                "secure": cookie.get("secure", True),
                "sameSite": same_site
            }
            normalized_cookies.append(normalized)
        
        # Inject cookies into context
        await self._context.add_cookies(normalized_cookies)
        logger.info(f"✅ Injected {len(normalized_cookies)} cookies into browser context")
    
    async def check_is_logged_in(self) -> bool:
        """
        Check if current page indicates successful Lexis login.
        
        Returns:
            True if logged in (on Lexis domain), False otherwise
        """
        if not self._page:
            logger.warning("❌ No page available for login check")
            return False
        
        current_url = self._page.url
        logger.info(f"🔍 Checking login status at: {current_url}")
        
        # Check URL contains Lexis domain
        is_lexis_domain = any(domain in current_url for domain in self.LEXIS_DOMAINS)
        if not is_lexis_domain:
            logger.info(f"❌ Not on Lexis domain (current: {current_url})")
            return False
        
        # Check if we're on login page (indicates cookies failed)
        if "login" in current_url.lower() or "signin" in current_url.lower():
            logger.info(f"❌ Redirected to login page - cookies invalid")
            return False
        
        # If we're on advance.lexis.com and NOT on login/signin, we're logged in!
        # Even error pages (like "Search Data Missing") prove authentication worked
        if "advance.lexis.com" in current_url:
            logger.info(f"✅ Logged in - on advance.lexis.com (authenticated)")
            return True
        
        # Check page content for login indicators
        try:
            # Multiple selectors to check for logged-in state
            page_content = await self._page.content()
            
            # Check for common logged-in indicators
            logged_in_indicators = [
                "search-box" in page_content.lower(),
                "user-menu" in page_content.lower(),
                "sign out" in page_content.lower(),
                "my workspace" in page_content.lower(),
                'data-testid="search' in page_content.lower()
            ]
            
            if any(logged_in_indicators):
                logger.info(f"✅ Logged in - found user indicators")
                return True
            
            # Try waiting for specific element
            try:
                await self._page.wait_for_selector("input[type='text'], textarea, [role='search']", timeout=3000)
                logger.info(f"✅ Logged in - found search input")
                return True
            except:
                pass
            
            logger.info(f"❌ Not logged in - no user indicators found")
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False

    async def close_robot(self):
        """Put the robot to sleep (release page back to pool)."""
        logger.info(f"🔄 close_robot() called - use_pool={self.use_pool}, has_browser={self._browser is not None}, has_page={self._page is not None}")
        
        if self.use_pool:
            # POOL MODE: release page but keep it open
            if self._page:
                if self._pool:
                     await self._pool.release_page(self._page)
                self._page = None
            logger.info("♻️ Page released to pool (kept alive)")
            return
        
        # Legacy: Close everything
        if self._context:
            # Save session for next time - ONLY if we're on Lexis domain
            try:
                # Check if page is still valid before accessing URL
                current_url = ""
                if self._page:
                    try:
                        if not self._page.is_closed():
                            current_url = self._page.url
                    except:
                        pass  # Page not accessible
                
                if current_url and any(domain in current_url for domain in self.LEXIS_DOMAINS):
                    storage = await self._context.storage_state()
                    with open(self.session_file, 'w') as f:
                        json.dump(storage, f)
                    logger.info("✅ Session cookies saved (Lexis authentication valid).")
                else:
                    logger.warning("⚠️ Not saving session - not on Lexis domain or page already closed")
                    # Remove invalid session file if it exists
                    if self.session_file.exists():
                        self.session_file.unlink()
                        logger.info("🗑️ Removed invalid session file")
            except Exception as e:
                logger.error(f"Failed to save session: {e}")
                
        if self._browser:
            try:
                await self._browser.close()
                logger.info("🤖 Robot Browser closed successfully")
            except Exception as close_error:
                logger.warning(f"⚠️ Browser was already closed: {close_error}")

    async def login_flow(self):
        """
        Handle the UM Library → EzProxy → CAS → Lexis authentication flow.
        
        CRITICAL: Authentication MUST follow this exact sequence:
        1. Navigate to UM Library Database Portal
        2. DOM click on "Lexis Advance® Malaysia" link
        3. Allow redirect to CAS (with service= parameter)
        4. Fill credentials on CAS page
        5. Wait for redirect chain: CAS → EzProxy → Lexis
        
        This flow generates the correct service tickets and session cookies.
        Direct CAS navigation will ALWAYS fail.
        """
        if not self._page:
            raise Exception("Robot not started")
        
        # Check if we already have a valid Lexis session
        try:
            if await self._check_existing_session():
                logger.info("⚡ Valid Lexis session found - skipping login")
                return
        except Exception:
            logger.info("No valid existing session - proceeding with fresh login")
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 1: Navigate to UM Library Database Portal (THE ENTRY POINT)
        # ═══════════════════════════════════════════════════════════════
        logger.info("📚 STEP 1: Navigating to UM Library Database Portal...")
        
        try:
            await self._page.goto(self.UM_LIBRARY_PORTAL_URL, timeout=self.timeout)
            await self._page.wait_for_load_state("domcontentloaded")
        except Exception as e:
            await self._capture_debug_state("step1_portal_failed")
            raise Exception(f"Failed to load UM Library Portal: {e}")
        
        logger.info(f"✅ Library portal loaded: {self._page.url}")
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 2: Find and Click "Lexis Advance® Malaysia" Link
        # ═══════════════════════════════════════════════════════════════
        logger.info("📚 STEP 2: Finding Lexis Advance® Malaysia link...")
        
        # Wait for page to fully render
        # await asyncio.sleep(2)  <-- REMOVED for speed

        
        lexis_link_selectors = [
            "a:has-text('Lexis Advance® Malaysia')",
            "a:has-text('Lexis Advance Malaysia')",
            "a:has-text('Lexis Advance')",
            "a[href*='lexis']",
            "text=Lexis Advance",
        ]
        
        link_clicked = False
        for selector in lexis_link_selectors:
            try:
                link = await self._page.wait_for_selector(selector, timeout=5000)
                if link:
                    logger.info(f"Found Lexis link with selector: {selector}")
                    await link.click()
                    link_clicked = True
                    break
            except Exception:
                continue
        
        if not link_clicked:
            await self._capture_debug_state("step2_lexis_link_not_found")
            raise Exception(
                "CRITICAL: Could not find 'Lexis Advance® Malaysia' link on library portal. "
                "The library page structure may have changed."
            )
        
        logger.info("✅ Clicked Lexis Advance link - waiting for redirect chain...")
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Wait for OpenAthens/CAS Login Page (via EzProxy redirect)
        # ═══════════════════════════════════════════════════════════════
        logger.info("🔐 STEP 3: Waiting for CAS login page (via EzProxy)...")
        
        # Give time for redirects to start
        await asyncio.sleep(1) # Reduced from 3s to 1s

        
        try:
            # Wait for CAS, Lexis, or OpenAthens Chooser
            await self._page.wait_for_url(
                lambda url: self.CAS_DOMAIN in url or \
                            "login.openathens.net" in url or \
                            any(d in url for d in self.LEXIS_DOMAINS),
                timeout=300000
            )
        except Exception:
            pass # Check URL below
            
        current_url = self._page.url
        
        # HANDLE OPENATHENS CHOOSER INTERCEPTION
        if "login.openathens.net" in current_url or "wayfinder" in current_url:
            logger.info(f"ℹ️ OpenAthens intermediate page (Attempting Institution Selection): {current_url}")
            
            try:
                # Wait for content to load
                await self._page.wait_for_load_state("domcontentloaded")
                
                # Preferred selector: the clickable div
                try:
                    logger.info("Clicking institution link...")
                    await self._page.click("div[role='link']:has-text('UM Staff')", timeout=10000, force=True)
                    clicked = True
                    logger.info("Successfully clicked UM Staff div link.")
                except Exception as e:
                    logger.debug(f"Primary selector click failed: {e}")
                    
                    # Try other selectors as fallback
                    for selector in [
                        "text=UM Staff and Students",
                        "text='UM Staff and Students'",
                        ".fa-chevron-circle-right"
                    ]:
                        try:
                            element = await self._page.wait_for_selector(selector, timeout=3000, state="visible")
                            if element:
                                await element.click(force=True)
                                clicked = True
                                logger.info(f"Clicked institution using: {selector}")
                                break
                        except:
                            continue
                
                if not clicked:
                    # Last ditch: JS check and click
                    logger.info("Last ditch JS click for institution...")
                    await self._page.evaluate("""
                        () => {
                            const elements = Array.from(document.querySelectorAll('*'));
                            const umLink = elements.find(
                                e => (e.textContent && e.textContent.includes('UM Staff')) || 
                                     (e.getAttribute && e.getAttribute('role') === 'link' && e.innerText.includes('Staff'))
                            );
                            if (umLink) {
                                umLink.scrollIntoView();
                                umLink.click();
                                return true;
                            }
                            return false;
                        }
                    """)
            except Exception as e:
                logger.warning(f"Institution selection attempt finished: {e}")
            
            # Now wait for redirect to CAS or Lexis
            logger.info("⏳ Waiting for final redirect to CAS or Lexis...")
            try:
                await self._page.wait_for_url(
                    lambda u: self.CAS_DOMAIN in u or any(d in u for d in self.LEXIS_DOMAINS), 
                    timeout=45000
                )
            except Exception:
                logger.info(f"Redirect from OpenAthens timed out. Current URL: {self._page.url}")
        
        current_url = self._page.url
        
        # Now validate where we are
        if self.EZPROXY_DOMAIN in current_url:
             # Loop wait if still on EzProxy
            logger.info("On EzProxy page - waiting for final redirect...")
            try:
                await self._page.wait_for_url(lambda u: self.CAS_DOMAIN in u, timeout=30000)
            except Exception:
                await self._capture_debug_state("step3_ezproxy_stuck")
                raise Exception(f"Stuck on EzProxy page: {current_url}")
        
        current_url = self._page.url
        # ALLOW login.openathens.net if it's the final destination (some versions of the flow stay there briefly)
        # but primarily we want CAS or Lexis.
        valid_destinations = [self.CAS_DOMAIN, "login.openathens.net"] + self.LEXIS_DOMAINS
        if not any(d in current_url for d in valid_destinations):
             await self._capture_debug_state("step3_unexpected_redirect")
             raise Exception(
                f"Unexpected redirect destination: {current_url}. "
                "Expected CAS login page, OpenAthens, or Lexis."
             )
        
        current_url = self._page.url
        logger.info(f"Current URL: {current_url}")
        
        # Check if we landed directly on Lexis (already authenticated)
        if any(domain in current_url for domain in self.LEXIS_DOMAINS):
            logger.info("⚡ Already authenticated - landed directly on Lexis!")
            return
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 3b: VALIDATE CAS URL has correct service= parameter
        # ═══════════════════════════════════════════════════════════════
        if self.CAS_DOMAIN in current_url:
            if "service=" not in current_url:
                await self._capture_debug_state("step3b_no_service_param")
                raise Exception(
                    "CRITICAL: CAS page reached WITHOUT service= parameter. "
                    "This means EzProxy redirect chain is broken. "
                    "The service parameter is REQUIRED for CAS to redirect back to Lexis."
                )
            logger.info("✅ CAS login page loaded with valid service parameter")
        
            # ═══════════════════════════════════════════════════════════════
            # STEP 4: Fill CAS Login Credentials
            # ═══════════════════════════════════════════════════════════════
            logger.info("🔑 STEP 4: Filling CAS credentials...")
            
            try:
                # Wait for login form
                await self._page.wait_for_selector("#login-form", timeout=300000)
                
                # Determine Domain Type from email
                domain_type = "Staff"
                if "@siswa" in self.username:
                    domain_type = "Student"
                
                # Select Domain (Important for server-side checks if any)
                try:
                    await self._page.select_option("select[name='domain']", label=domain_type)
                    
                    # Verify selection
                    selected_val = await self._page.evaluate("document.getElementById('domain').value")
                    logger.info(f"Selected '{domain_type}' from status dropdown (Value: {selected_val})")
                except Exception as e:
                    logger.warning(f"Could not select domain dropdown: {e}")

                # Fill Full Username
                await self._page.fill("#inputEmail", self.username)
                
                # Verify username
                filled_user = await self._page.evaluate("document.getElementById('inputEmail').value")
                logger.info(f"Filled full username: {filled_user}")
                
                # Fill Password
                await self._page.fill("#inputPassword", self.password)
                logger.info("Filled password")

                # Submit form directly via JS to bypass 'doMerge' username appending logic
                logger.info("🚀 Submitting form directly via JS...")
                await self._page.evaluate("document.getElementById('login-form').submit()")
                
            except Exception as e:
                await self._capture_debug_state("step4_login_form_failed")
                raise Exception(f"CAS login form interaction failed: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 5: Wait for Redirect Chain (CAS → EzProxy → Lexis)
        # ═══════════════════════════════════════════════════════════════
        logger.info("🔄 STEP 5: Waiting for redirect chain to Lexis...")
        
        try:
            # Wait for Lexis domain with extended timeout for complex redirects
            await self._page.wait_for_url(
                lambda url: any(domain in url for domain in self.LEXIS_DOMAINS),
                timeout=180000
            )
        except Exception:
            current_url = self._page.url
            page_content = await self._page.content()
            page_title = await self._page.title()
            
            # Check specific failure states
            if "Log In Successful" in page_content or "does not know about your target destination" in page_content:
                await self._capture_debug_state("step5_cas_stranded")
                raise Exception(
                    "AUTHENTICATION FAILED: CAS login succeeded but redirect chain is broken. "
                    "The message 'CAS does not know about your target destination' indicates "
                    "the service= parameter was invalid or not recognized. "
                    "Ensure access was initiated from UM Library Portal link click."
                )
            
            if "error" in current_url.lower() or "denied" in page_content.lower():
                await self._capture_debug_state("step5_access_denied")
                raise Exception(f"Access denied or error during redirect: {current_url}")
            
            if "invalid" in page_content.lower() or "incorrect" in page_content.lower():
                await self._capture_debug_state("step5_invalid_credentials")
                raise Exception("Invalid credentials - please check LEXIS_USERNAME and LEXIS_PASSWORD in .env")
            
            await self._capture_debug_state("step5_redirect_failed")
            raise Exception(
                f"Redirect chain did not complete. Current URL: {current_url}. "
                f"Expected Lexis domain. Page title: {page_title}"
            )
        
        logger.info(f"✅ Successfully reached Lexis: {self._page.url}")
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 6: Verify Lexis Dashboard is Fully Loaded
        # ═══════════════════════════════════════════════════════════════
        logger.info("🔍 STEP 6: Verifying Lexis dashboard...")
        
        # Wait for page to stabilize
        # Wait for page to stabilize
        await self._page.wait_for_load_state("domcontentloaded")
        # await asyncio.sleep(2) <-- REMOVED for speed

        
        if not await self.check_is_logged_in():
            await self._capture_debug_state("step6_lexis_not_loaded")
            raise Exception(
                "Reached Lexis domain but dashboard elements not found. "
                "Authentication may be incomplete or Lexis page structure changed."
            )
        
        logger.info("🎉 Authentication complete - Lexis dashboard verified!")

    async def re_authenticate(self) -> bool:
        """
        Force a fresh re-authentication when session has expired (401 Unauthorized).
        
        Unlike login_flow(), this ALWAYS does a fresh login — it skips the
        existing-session check since we know the session is dead.
        
        Returns:
            True if re-authentication succeeded, False otherwise
        """
        logger.info("🔄 RE-AUTHENTICATING: Session expired (401), forcing fresh login...")
        
        if not self._page or self._page.is_closed():
            logger.error("❌ Cannot re-authenticate: page is closed")
            return False
        
        try:
            # Navigate to UM Library portal to start fresh auth flow
            # We call login_flow() but first invalidate any session check
            # by navigating away from Lexis domain
            await self._page.goto("about:blank", timeout=5000)
            await asyncio.sleep(0.5)
            
            # Now run the full login flow (will skip existing session check
            # because we're on about:blank, not on advance.lexis.com)
            await self.login_flow()
            
            # Verify we're back on Lexis search page
            if await self.check_is_logged_in():
                logger.info("✅ RE-AUTHENTICATION SUCCESSFUL — session refreshed")
                return True
            else:
                logger.warning("⚠️ Re-authentication completed but login check failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Re-authentication failed: {e}", exc_info=True)
            return False

    @staticmethod
    def _is_auth_error(error_msg: str) -> bool:
        """
        Check if an error message indicates a session/auth expiry.
        
        Args:
            error_msg: Error string from fetch_judgment_by_citation or similar
            
        Returns:
            True if this looks like a 401/session expiry issue
        """
        if not error_msg:
            return False
        error_lower = error_msg.lower()
        auth_indicators = [
            "authentication required",
            "401",
            "unauthorized",
            "sign in",
            "signin",
            "session expired",
            "login required",
            "please enter a valid id",
            "document page requires authentication",
        ]
        return any(indicator in error_lower for indicator in auth_indicators)

    async def _check_existing_session(self) -> bool:
        """
        Check if we have a valid existing Lexis session.
        Navigate directly to Lexis Search and verify access.
        """
        logger.info("Checking for existing valid session via Direct URL...")
        
        # KEY OPTIMIZATION: Go directly to Search Page
        try:
            # If already on Search Page, just check status
            if "advance.lexis.com/search" in self._page.url:
                logger.info("Already on search page - checking status directly")
            else:
                await self._page.goto("https://advance.lexis.com/search", timeout=20000)
            
            await self._page.wait_for_load_state("domcontentloaded")

            
            # If we are redirected to signin, check_is_logged_in will return False
            if await self.check_is_logged_in():
                logger.info("✅ Direct Search Navigation Successful!")
                return True
        except Exception as e:
            logger.warning(f"Session check navigation failed: {e}")
            
        return False

    async def _capture_debug_state(self, prefix: str):
        """Capture screenshot and HTML for debugging failed states."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.debug_dir.mkdir(exist_ok=True)
            
            # Screenshot
            screenshot_path = self.debug_dir / f"{prefix}_{timestamp}.png"
            await self._page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"📸 Debug screenshot saved: {screenshot_path}")
            
            # HTML content
            html_path = self.debug_dir / f"{prefix}_{timestamp}.html"
            content = await self._page.content()
            html_path.write_text(content, encoding='utf-8')
            logger.info(f"📄 Debug HTML saved: {html_path}")
            
            # Log current state
            logger.info(f"🔗 Current URL: {self._page.url}")
            logger.info(f"📑 Page Title: {await self._page.title()}")
            
        except Exception as e:
            logger.warning(f"Could not capture debug state: {e}")

    async def check_is_logged_in(self) -> bool:
        """Check if we are successfully on the Lexis Search Page."""
        if not self._page: 
            return False
        try:
            # Verify we're on Lexis domain first
            current_url = self._page.url
            
            # Explicitly fail if we are on the Sign In page
            if "signin.lexisnexis.com" in current_url:
                logger.info("ℹ️ Detected Sign In page - not logged in")
                return False
                
            if not any(domain in current_url for domain in self.LEXIS_DOMAINS):
                return False
            
            # Check for Lexis dashboard specific elements
            # AVOID generic inputs that might match cookie banners (like type='search')
            lexis_indicators = [
                "#searchTerms",                 # Verified ID from debug capture
                "[placeholder*='Enter terms']", # Verified Placeholder
                "textarea[name='search']",      
                "input[name='search']",
                "#mainSearch", 
                "[data-testid='search-input']",
                ".searchbox",
                # NEW: Detection for Results Page / Doc View
                "ol.search-results",
                ".search-results",
                "#results-list",
                ".document-view",
            ]
            
            # First check: Do we see the Sign In form?
            if await self._page.is_visible("#userid", timeout=500):
                logger.info("ℹ️ Detected User ID field - not logged in")
                return False
            
            # Second check: Do we see the dashboard or any valid Lexis view?
            # Optimization: Try to find ANY indicator in a single JS execution
            indicators_js = json.dumps(lexis_indicators)
            found_indicator = await self._page.evaluate(f"""
                (indicators) => {{
                    return indicators.some(s => !!document.querySelector(s));
                }}
            """, lexis_indicators)
            
            if found_indicator:
                # Still verify visibility of one just to be sure Playwright is ready
                # but we use a very short timeout now
                logger.info(f"✅ Lexis verified via indicators")
                return True
            
            # If we're on advance.lexis.com and NOT on signin, we're authenticated!
            # Even error pages prove authentication worked
            if "advance.lexis.com" in current_url:
                logger.info(f"✅ Logged in - on advance.lexis.com (authenticated via cookies)")
                return True
            
            # DEBUG: If we reached here, we are on Lexis domain but couldn't find indicators
            logger.warning(f"⚠️ Check Failed on URL: {current_url}")
            try:
                # Save debug snapshot to see what we missed
                timestamp = datetime.now().strftime("%H%M%S") 
                await self._page.screenshot(path=str(self.debug_dir / f"auth_check_fail_{timestamp}.png"))
            except: pass
            
            return False
        except Exception:
            return False

    async def search(self, query: str, country: str = "Malaysia", filters: Dict = None, user_id: str = None) -> List[Dict]:
        """
        Execute the search robot with comprehensive filter support.
        
        Args:
            query: Search query
            country: Jurisdiction filter
            filters: Additional filters
            user_id: User ID for cookie lookup (if available, use cookies instead of UM Library)
        """
        if filters is None:
            filters = {}
            
        try:
            search_start = datetime.now()
            # 1. Acquire Page (Persistent or New)
            await self.start_robot()
            
            # =========================================================================
            # PRIORITY 1: CHECK FOR SAVED COOKIES AND INJECT BEFORE NAVIGATION
            # If user has saved cookies, inject them FIRST before trying UM Library
            # =========================================================================
            cookies_injected = False
            if user_id:
                try:
                    from database import get_sync_db
                    from models.lexis_credentials import LexisCredentials
                    from datetime import datetime as dt
                    
                    logger.info(f"🔍 Checking for saved cookies for user: {user_id}")
                    
                    # Get cookies from database
                    with next(get_sync_db()) as db:
                        creds = db.query(LexisCredentials).filter(LexisCredentials.user_id == user_id).first()
                        
                        if creds and creds.cookies_encrypted:
                            # Check if expired
                            if creds.cookies_expires_at and dt.utcnow() < creds.cookies_expires_at:
                                cookies = creds.get_cookies()
                                if cookies:
                                    logger.info(f"✅ Found valid saved cookies - injecting...")
                                    await self.inject_cookies(cookies)
                                    cookies_injected = True
                                    logger.info(f"🚀 Using cookie authentication (FAST MODE)")
                                    
                                    # Navigate to dashboard to apply cookies
                                    logger.info(f"📄 Navigating to Lexis dashboard with cookies...")
                                    await self._page.goto("https://advance.lexis.com/firsttime", timeout=30000, wait_until="domcontentloaded")
                                    # Wait for page to settle
                                    await self._page.wait_for_load_state("networkidle", timeout=15000)
                                    final_url = self._page.url
                                    logger.info(f"✅ Navigation complete - now at: {final_url}")
                                    
                                    # CRITICAL CHECK: Are we actually logged in?
                                    is_logged_in = await self.check_is_logged_in()
                                    logger.info(f"🔐 Login status after cookie injection: {is_logged_in}")
                                    
                                    if not is_logged_in:
                                        logger.warning(f"❌ Cookies did NOT authenticate! Will fall back to UM Library")
                                        cookies_injected = False  # Force fallback to UM Library
                            else:
                                logger.info(f"⏰ Saved cookies expired - will use UM Library")
                        else:
                            logger.info(f"📭 No saved cookies found - will use UM Library")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Cookie lookup failed: {e} - will use UM Library")
            
            # =========================================================================
            # OPTIMISTIC SEARCH STRATEGY
            # Attempt to search immediately without verifying session state.
            # If we can find the search box and type, we are logged in.
            # If we fail, we assume session is dead and trigger re-login.
            # =========================================================================
            
            search_selectors = [
                 # From actual DOM inspection - EXACT structure
                 "div.expandingTextarea.shown textarea#searchTerms",
                 "div.expandingTextarea textarea#searchTerms",
                 "textarea#searchTerms",
                 "textarea[aria-label='Enter Search Term With Autocomplete Suggestion']",
                 "textarea[id='searchTerms']",
                 "textarea[placeholder='Enter terms, publications, or a citation']",
                 
                 # Fallbacks
                 "div.expandingTextarea textarea",
                 "[placeholder*='Enter terms']",
                 "#searchTerms", 
                 ".searchcontainer_desktop textarea",
             ]
            
            # Try to find input immediately
            search_input = None
            try:
                # 1.1 If already on Lexis, check visibility first without navigation
                current_url = self._page.url
                
                # Check if we are already on a results page or search page
                is_on_lexis = any(d in current_url for d in self.LEXIS_DOMAINS)
                
                if not is_on_lexis or current_url == "about:blank":
                    logger.info(f"📄 Page at {current_url} - Navigating to Lexis Dashboard...")
                    # Navigate to the actual dashboard page
                    await self._page.goto("https://advance.lexis.com/firsttime", timeout=20000)
                    # Wait for page to fully load
                    await self._page.wait_for_load_state("networkidle", timeout=10000)
                    final_url = self._page.url
                    logger.info(f"✅ Page loaded at {final_url}")
                    
                    # Debug: Check page title and content
                    page_title = await self._page.title()
                    logger.info(f"🔍 Page title: {page_title}")
                    
                    # Check if we got redirected to login
                    if "signin" in final_url.lower() or "login" in final_url.lower():
                        logger.warning(f"⚠️ Redirected to login page! Cookies may be invalid or insufficient")
                    
                    # Take screenshot for debugging
                    try:
                        screenshot_path = "lexis_debug_screenshot.png"
                        await self._page.screenshot(path=screenshot_path)
                        logger.info(f"📸 Screenshot saved to {screenshot_path}")
                    except:
                        pass
                    
                    # Debug: Check if the search container exists at all
                    try:
                        container = await self._page.query_selector("div.expandingTextarea")
                        if container:
                            logger.info(f"✅ Found expandingTextarea container")
                            is_visible = await container.is_visible()
                            logger.info(f"📊 Container visible: {is_visible}")
                        else:
                            logger.warning(f"❌ expandingTextarea container NOT found in DOM")
                    except Exception as e:
                        logger.warning(f"⚠️ Container check failed: {e}")
                
                # Try to find search box with a shorter but effective wait
                for selector in search_selectors:
                    try:
                        # Use wait_for_selector with shorter timeout for each
                        element = await self._page.wait_for_selector(selector, timeout=5000, state="visible")
                        if element:
                            search_input = element
                            logger.info(f"⚡ Found search box via: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {str(e)[:50]}")
                        continue
                
                if search_input:
                    logger.info("⚡ OPTIMISTIC SEARCH: Found search box immediately! Skipping login flow.")
                else:
                    raise Exception("Search box not visible after optimistic checks")

                    
            except Exception as e:
                # If optimistic check failed, fall back to safe login flow
                logger.warning(f"⚠️ Optimistic search failed: {str(e)}")
                logger.info(f"🔄 Falling back to UM Library login flow...")
                await self.login_flow()
                logger.info(f"✅ Login flow completed, now at: {self._page.url}")
                
                # Wait for Lexis dashboard to fully load after login redirects
                try:
                    await self._page.wait_for_load_state("domcontentloaded", timeout=30000)
                    logger.info("📄 DOM content loaded after login")
                except Exception as load_err:
                    logger.warning(f"⚠️ DOM load wait timed out: {load_err}")
                
                try:
                    await self._page.wait_for_load_state("networkidle", timeout=15000)
                    logger.info("🌐 Network idle after login")
                except Exception as idle_err:
                    logger.warning(f"⚠️ Network idle wait timed out: {idle_err}")
                
                # Extra settle time for Lexis JS to render the search box
                await asyncio.sleep(3)
                
                logger.info(f"🔍 Post-login page URL: {self._page.url}")
                logger.info(f"🔍 Post-login page title: {await self._page.title()}")
                
                # Retry finding search input after login with longer timeouts
                for selector in search_selectors:
                    try:
                        element = await self._page.wait_for_selector(selector, timeout=10000, state="visible")
                        if element:
                            search_input = element
                            logger.info(f"✅ Found search box post-login via: {selector}")
                            break
                    except Exception:
                        continue
                
                # If still not found, try navigating to search page directly
                if not search_input:
                    logger.info("🔄 Search box not found - navigating to search page directly...")
                    try:
                        await self._page.goto("https://advance.lexis.com/search", timeout=30000)
                        await self._page.wait_for_load_state("domcontentloaded", timeout=15000)
                        await asyncio.sleep(2)
                        
                        for selector in search_selectors:
                            try:
                                element = await self._page.wait_for_selector(selector, timeout=10000, state="visible")
                                if element:
                                    search_input = element
                                    logger.info(f"✅ Found search box after direct navigation via: {selector}")
                                    break
                            except Exception:
                                continue
                    except Exception as nav_err:
                        logger.warning(f"⚠️ Direct search page navigation failed: {nav_err}")
            
            if not search_input:
                await self._capture_debug_state("search_input_not_found")
                raise Exception("Could not find search input on Lexis dashboard")
            
            t1 = datetime.now()
            logger.info(f"⏱️ Input found in {(t1 - search_start).total_seconds():.2f}s")

            
            
            # Clear existing text (important for persistent page)
            await search_input.fill("")
            await asyncio.sleep(0.5)
            
            # COMPREHENSIVE FILTER AUGMENTATION
            # Since we can't reliably interact with Lexis filter UI, augment query with keywords
            final_query = query
            augmentations = []
            
            # Country/Jurisdiction
            if country and country.lower() != "malaysia":
                augmentations.append(country)
            
            # Court level
            court = filters.get("court", "").strip().lower()
            court_map = {"federal": "Federal Court", "appeal": "Court of Appeal", "high": "High Court"}
            if court in court_map:
                augmentations.append(court_map[court])
                logger.info(f"Adding court filter: {court_map[court]}")
            
            # Build final query
            if augmentations:
                final_query = " ".join(augmentations) + " " + query
                logger.info(f"Augmented Query: '{final_query}'")

            await search_input.fill(final_query)
            await search_input.press("Enter")
            
            # 3. Wait for Results
            logger.info("Waiting for results...")
            t2 = datetime.now()
            logger.info(f"⏱️ Search submitted in {(t2 - t1).total_seconds():.2f}s")

            # await asyncio.sleep(3) <-- CRITICAL OPTIMIZATION: REMOVED FIXED SLEEP

            
            # Lexis result items often have class 'search-result' or similar
            # We wait for *something* to appear
            try:
                # Wait for results OR document view (direct hit)
                await self._page.wait_for_selector("a[href*='document'], .doc-title, article.item, .noresults, .document-view, #api_content", timeout=10000)
                
                t3 = datetime.now()
                logger.info(f"⏱️ Results appeared in {(t3 - t2).total_seconds():.2f}s")
                
                # CHECK FOR DIRECT HIT (Document Page)
                if "/document" in self._page.url or await self._page.is_visible(".document-view") or await self._page.is_visible(".ss-header-content"):
                    logger.info("⚡ Direct Document Hit Detected!")
                    current_url = self._page.url
                    # Extract single result specifics
                    title = await self._page.title()
                    # Try to get cleaner title from H1 if possible
                    try:
                        h1 = await self._page.query_selector("h1")
                        if h1: title = await h1.inner_text()
                    except: pass
                    
                    return [{
                        "title": title.replace(" - Lexis Advance", "").strip(),
                        "citation": query, # Best guess for citation is the query itself in this case
                        "court": "Direct Document",
                        "judgment_date": datetime.now().strftime("%Y-%m-%d"),
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "summary": "Direct document access via citation search.",
                        "link": current_url, # The EXACT link user wants
                        "relevance_score": 1.0,
                        "binding": False
                    }]

            except Exception as e:
                logger.info(f"⚠️ Result wait timed out or failed: {e}")
                # Save debug snapshot to see what we missed
                await self._capture_debug_state("search_results_debug")
                
                page_content = await self._page.content()
                if "no results" in page_content.lower() or "0 results" in page_content.lower():
                    logger.info("Search returned no results")
                    return []
                pass
            
            t3 = datetime.now() # Fallback for extraction timing

            
            # =========================================================================
            # TURBO MODE: Javascript Injection for High-Speed Extraction
            # Eliminates 200+ round-trips to browser.
            # =========================================================================
            logger.info("🚀 Executing Turbo Extraction (Javascript Injection)...")
            
            js_payload = r"""
            () => {
                // 1. SELECT ALL RESULT CARDS
                // Try multiple patterns for the parent container
                let cards = Array.from(document.querySelectorAll("ol.search-results > li[data-idx], .search-result, li.search-result"));
                
                // If the above fails, try finding containers that HAVE a doc-title
                if (cards.length === 0) {
                    cards = Array.from(document.querySelectorAll("h2.doc-title")).map(el => {
                        // Find the closest parent that likely contains the whole card
                        return el.closest('li') || el.closest('.result-card') || el.parentElement;
                    });
                }

                const results = [];
                const seenCitations = new Set();
                
                cards.forEach((card) => {
                    try {
                        // 2. EXTRACT TITLE
                        let title = "";
                        const titleEl = card.querySelector("h2.doc-title a, h2.doc-title, .doc-title a");
                        if (titleEl) {
                            title = titleEl.innerText.trim();
                        } else {
                            // Fallback: Find first link that looks like a case name (v / vs)
                            const vLink = Array.from(card.querySelectorAll("a")).find(a => {
                                const t = a.innerText.toUpperCase();
                                return (t.includes(" V ") || t.includes(" VS ")) && t.length > 10;
                            });
                            if (vLink) title = vLink.innerText.trim();
                        }
                        
                        // Clean title
                        if (title) {
                            title = title.split('\\n')[0].trim();
                            // If title is just a snippet starting with '...', it's probably wrong
                            if (title.startsWith('...')) title = "";
                        }
                        
                        if (!title) title = "Unknown Case";

                        // 3. EXTRACT CITATION
                        let citation = "No Citation";
                        const allCitLinks = Array.from(card.querySelectorAll("p.onecase a, .citationtitle, span.citation, .citation"));
                        for (let cl of allCitLinks) {
                            const text = cl.innerText.trim();
                            if (text.match(/\[\d{4}\]/) || text.match(/\d+\s+[A-Z]+\s+\d+/)) {
                                citation = text;
                                break;
                            }
                        }
                        
                        if (citation === "No Citation") {
                            // Regex fallback on text content
                            const match = card.innerText.match(/\[(\d{4})\]\s+(MLJU|MLJ)\s+(\d+)/i);
                            if (match) citation = match[0];
                        }
                        
                        // Deduplicate
                        if (seenCitations.has(citation) && citation !== "No Citation") return;
                        seenCitations.add(citation);

                        // 4. EXTRACT METADATA (Court, Date)
                        let court = "Unknown Court";
                        let date = "Unknown Date";
                        const metaDl = card.querySelector("aside.metadata dl, .metadata dl, dl");
                        if (metaDl) {
                            const dts = Array.from(metaDl.querySelectorAll("dt"));
                            const dds = Array.from(metaDl.querySelectorAll("dd"));
                            dts.forEach((dt, i) => {
                                if (i >= dds.length) return;
                                const label = dt.innerText.toLowerCase();
                                const val = dds[i].innerText.trim();
                                if (label.includes("court")) court = val;
                                if (label.includes("date")) date = val;
                            });
                        }

                        // 5. EXTRACT SUMMARY (Teaser)
                        let summary = "";
                        const summaryEl = card.querySelector("p.passage, p.min.vis, .snippet, .result-text");
                        if (summaryEl) {
                            summary = summaryEl.innerText.trim();
                        } else {
                            // Take first 200 chars of non-metadata text
                            summary = card.innerText.substring(0, 300).replace(/\\s+/g, ' ').trim();
                        }
                        
                        // Cleanup summary: Remove common UI labels
                        ["Show/hide", "Folders", "View document", "CaseAnalysis"].forEach(s => {
                            summary = summary.replace(s, "");
                        });

                        // 6. GENERATE DEEP LINK (Proxy-Aware)
                        let link = "";
                        
                        // Strategy 1: Extract URN from checkbox (Most reliable for SPA)
                        const urnInput = card.querySelector("input[data-docid]");
                        if (urnInput) {
                            const urn = urnInput.getAttribute("data-docid");
                            // Construct standard Lexis deep link for Malaysian cases
                            if (urn) {
                                // We use 'cases-my' as default path for cases. 
                                // pdmfid=1522468 is the standard product ID for Lexis Advance
                                link = "https://advance.lexis.com/document?pddocfullpath=/shared/document/cases-my/" + encodeURIComponent(urn) + "&pdmfid=1522468";
                            }
                        }

                        // Strategy 2: If URN failed, try "View document" link (Fallback)
                        if (!link) {
                             const viewDocLink = Array.from(card.querySelectorAll("a")).find(a => {
                                const t = (a.textContent || a.innerText || "").toLowerCase().trim();
                                return t.includes("view document") || t.includes("view this passage");
                            });
                             if (viewDocLink && viewDocLink.href && !viewDocLink.href.includes("#")) {
                                link = viewDocLink.href;
                            }
                        }

                        // Strategy 3: Direct href search
                        if (!link) {
                            const docHrefLink = Array.from(card.querySelectorAll("a")).find(a => {
                                return a.href && a.href.includes("/document?");
                            });
                            if (docHrefLink) link = docHrefLink.href;
                        }

                        // Strategy 4: Fallback to Search URL
                        if (!link || link === "#") {
                             const origin = window.location.origin;
                             // Just send them to valid search results instead of broken link
                             if (citation !== "No Citation") {
                                 link = origin + "/search?q=" + encodeURIComponent(citation);
                             } else {
                                 link = origin + "/search?q=" + encodeURIComponent(title);
                             }
                        }
                        
                        let debug_html = "";
                        if (!link || link.includes("/search?")) {
                                debug_html = card.outerHTML;
                        }

                        results.push({
                            title,
                            citation,
                            court,
                            judgment_date: date,
                            date, 
                            summary: summary.substring(0, 500),
                            link,
                            relevance_score: 0.5,
                            debug_html
                        });



                    } catch (e) {
                         // Skip failed card
                    }
                });
                return results;
            }
            """
            
            t_extraction_start = datetime.now() # New timing variable for extraction
            raw_results = await self._page.evaluate(js_payload)
            t4 = datetime.now()
            logger.info(f"⏱️ Extraction completed in {(t4 - t_extraction_start).total_seconds():.2f}s")
            
            logger.info(f"✅ Turbo Extraction complete. Found {len(raw_results)} cases.")

            # FALLBACK: If 0 results but URL is a document, treat as Direct Hit
            if len(raw_results) == 0 and ("/document" in self._page.url or "pddocfullpath" in self._page.url):
                 logger.info("⚡ Fallback: Zero results but URL indicates Document Page. Treating as Direct Hit.")
                 current_url = self._page.url
                 title = await self._page.title()
                 try:
                     h1 = await self._page.query_selector("h1")
                     if h1: title = await h1.inner_text()
                 except: pass
                 
                 raw_results = [{
                    "title": title.replace(" - Lexis Advance", "").strip(),
                    "citation": query,
                    "court": "Direct Document",
                    "judgment_date": datetime.now().strftime("%Y-%m-%d"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "summary": "Direct document access via citation search.",
                    "link": current_url,
                    "relevance_score": 1.0,
                    "binding": False
                 }]
            
            results = []
            for res in raw_results: # Use raw_results here
                if res.get('debug_html'):
                    try:
                        debug_path = self.debug_dir / f"card_dump_{datetime.now().strftime('%H%M%S_%f')}.html"
                        debug_path.write_text(res['debug_html'], encoding='utf-8')
                        logger.info(f"🐛 Saved debug card HTML to {debug_path}")
                    except Exception as e:
                        logger.warning(f"Failed to save debug HTML: {e}")

                # Python-side Relevance Scoring (Fast enough)
                title_lower = res.get('title', '').lower()
                summary_lower = res.get('summary', '').lower()
                query_terms = query.lower().split()
                
                score = 0.5
                for term in query_terms:
                    # Title matches weight more
                    if term in title_lower: score += 0.15
                    # Summary matches
                    score += summary_lower.count(term) * 0.03
                
                # Recency bonus
                if "2026" in res.get('judgment_date', ''): score += 0.1
                elif "2025" in res.get('judgment_date', ''): score += 0.05
                
                res['relevance_score'] = min(score, 0.99)
                results.append(res)
                
            return results

        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"🚫 Research disabled: {e}")
            raise e
        except Exception as e:
            logger.error(f"Robot failed: {e}")
            try:
                # PANIC CAPTURE
                debug_file = self.debug_dir / "panic_dump.html"
                content = await self._page.content()
                debug_file.write_text(content, encoding='utf-8')
                logger.info(f"Panic capture saved to {debug_file}")
            except:
                pass
            raise e # Strict Real Data
        finally:
            await self.close_robot()
    
    async def fetch_judgment_by_citation(self, citation: str, case_title: str = "Unknown") -> Dict[str, Any]:
        """
        ⭐ OPTION B: Fetch judgment by searching citation in the search box.
        
        CRITICAL DESIGN:
        - Assumes self._page is ALREADY on an authenticated Lexis page with a search box
        - NEVER calls page.goto() — that causes browser crashes
        - After extraction, calls page.go_back() to return to search results
        - Caller is responsible for browser lifecycle (start_robot/close_robot)
        
        Flow: Find search box → Clear → Type citation → Enter → Click result → Extract → Back
        
        Args:
            citation: Case citation (e.g., "[2023] 1 MLJ 456")
            case_title: Optional case title for logging
            
        Returns:
            Dictionary with judgment data (same format as fetch_full_judgment)
        """
        try:
            if not citation or citation == "No Citation":
                return {
                    "success": False,
                    "error": "No citation available for search",
                    "full_text": "",
                    "word_count": 0
                }
            
            logger.info(f"🔍 Fetching by CITATION: {citation} ({case_title[:50]})")
            
            # Verify page is alive
            if not self._page or self._page.is_closed():
                return {
                    "success": False,
                    "error": "Browser page is closed - cannot fetch",
                    "full_text": "",
                    "word_count": 0
                }
            
            current_url = self._page.url
            logger.info(f"   Current page: {current_url}")
            
            # ─────────────────────────────────────────────────────────
            # STEP 0: Early auth check — detect if session expired
            # ─────────────────────────────────────────────────────────
            if "signin.lexisnexis.com" in current_url or "login" in current_url.lower():
                logger.warning(f"   ⚠️ Page redirected to login — session expired!")
                return {
                    "success": False,
                    "error": "401 Unauthorized — session expired, re-authentication needed",
                    "full_text": "",
                    "word_count": 0
                }
            
            # ─────────────────────────────────────────────────────────
            # STEP 1: Find the search box (should already be on page)
            # ─────────────────────────────────────────────────────────
            search_selectors = [
                "textarea#searchTerms",
                "div.expandingTextarea textarea#searchTerms",
                "textarea[id='searchTerms']",
                "textarea[aria-label*='Search']",
                "#searchTerms",
                "div.expandingTextarea textarea",
                "[placeholder*='Enter terms']",
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await self._page.wait_for_selector(selector, timeout=5000, state="visible")
                    if search_input:
                        logger.info(f"   ✅ Found search box: {selector}")
                        break
                except:
                    continue
            
            if not search_input:
                # Last resort: try clicking on the search area to make textarea appear
                try:
                    search_area = await self._page.query_selector("div.expandingTextarea, .search-box, .searchcontainer_desktop")
                    if search_area:
                        await search_area.click()
                        await asyncio.sleep(0.5)
                        search_input = await self._page.wait_for_selector("textarea#searchTerms", timeout=3000, state="visible")
                except:
                    pass
            
            if not search_input:
                page_title = await self._page.title()
                logger.warning(f"⚠️ Could not find search box on page: {page_title} ({self._page.url})")
                return {
                    "success": False,
                    "error": f"Search box not found on page ({page_title})",
                    "full_text": "",
                    "word_count": 0
                }
            
            # ─────────────────────────────────────────────────────────
            # STEP 2: Clear search box and type citation
            # ─────────────────────────────────────────────────────────
            await search_input.click()
            await asyncio.sleep(0.3)
            
            # Triple-click to select all text, then delete
            await search_input.click(click_count=3)
            await asyncio.sleep(0.1)
            await self._page.keyboard.press("Control+A")
            await asyncio.sleep(0.1)
            await self._page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)
            
            # Verify the box is clear
            try:
                current_value = await search_input.input_value()
                if current_value:
                    await search_input.fill("")
                    await asyncio.sleep(0.2)
            except:
                pass
            
            # Type citation in quotes for exact match
            citation_query = f'"{citation}"'
            await search_input.type(citation_query, delay=30)
            logger.info(f"   ⌨️ Typed: {citation_query}")
            await asyncio.sleep(0.3)
            
            # ─────────────────────────────────────────────────────────
            # STEP 3: Submit search and wait for results
            # ─────────────────────────────────────────────────────────
            await self._page.keyboard.press("Enter")
            logger.info(f"   ⏳ Waiting for citation search results...")
            
            # Wait for results or direct document hit
            await asyncio.sleep(2)
            
            # Check if we got a direct document hit (citation resolved to single doc)
            is_document_page = False
            try:
                new_url = self._page.url
                if "/document" in new_url or "pddocfullpath" in new_url:
                    is_document_page = True
                    logger.info(f"   ⚡ Direct document hit! URL: {new_url[:80]}...")
            except:
                pass
            
            if not is_document_page:
                # Wait for search results list
                result_selectors = [
                    "a[href*='document'], .doc-title",
                    "ol.search-results > li",
                    "li[data-idx]",
                    "h2.doc-title",
                    ".noresults",
                ]
                
                results_found = False
                for sel in result_selectors:
                    try:
                        await self._page.wait_for_selector(sel, timeout=10000)
                        results_found = True
                        break
                    except:
                        continue
                
                if not results_found:
                    # Check for no results
                    try:
                        page_text = await self._page.evaluate("() => document.body.innerText.toLowerCase()")
                        if "no results" in page_text or "0 results" in page_text:
                            logger.warning(f"   ⚠️ No results for citation: {citation}")
                            return {
                                "success": False,
                                "error": f"No search results for citation: {citation}",
                                "full_text": "",
                                "word_count": 0
                            }
                        if "sign in" in page_text or "password" in page_text:
                            return {
                                "success": False,
                                "error": "Authentication required",
                                "full_text": "",
                                "word_count": 0
                            }
                    except:
                        pass
                    
                    logger.warning(f"   ⚠️ Results page did not load for: {citation}")
                    return {
                        "success": False,
                        "error": f"Results page failed to load for citation: {citation}",
                        "full_text": "",
                        "word_count": 0
                    }
                
                # ─────────────────────────────────────────────────────────
                # STEP 4: Click first result to open document
                # ─────────────────────────────────────────────────────────
                logger.info(f"   📄 Clicking first result...")
                
                first_result_selectors = [
                    "h2.doc-title a",
                    "li[data-idx] h2 a",
                    "ol.search-results li a[href*='document']",
                    "a[href*='/document?']",
                    ".doc-title a",
                    "li.search-result a:first-of-type",
                ]
                
                clicked = False
                for selector in first_result_selectors:
                    try:
                        first_result = await self._page.wait_for_selector(selector, timeout=5000, state="visible")
                        if first_result:
                            await first_result.click()
                            clicked = True
                            logger.info(f"   ✅ Clicked result: {selector}")
                            break
                    except:
                        continue
                
                if not clicked:
                    logger.warning(f"   ⚠️ Could not click any result for: {citation}")
                    return {
                        "success": False,
                        "error": f"Could not click search result for citation: {citation}",
                        "full_text": "",
                        "word_count": 0
                    }
                
                # Wait for document page to load
                await asyncio.sleep(2)
            
            # ─────────────────────────────────────────────────────────
            # STEP 5: Wait for document content to load
            # ─────────────────────────────────────────────────────────
            try:
                await self._page.wait_for_load_state("domcontentloaded", timeout=15000)
            except:
                logger.debug("   DOM content loaded timeout (continuing...)")
            
            # Wait a bit more for JS-rendered content
            await asyncio.sleep(1)
            
            # Try waiting for the actual document content element
            try:
                await self._page.wait_for_selector(
                    '[data-cy="document-content"], #documentcontent, .document-content-wrapper, #api_content',
                    timeout=10000
                )
                logger.info(f"   ✅ Document content element found")
            except:
                logger.debug("   Document content selector timeout (will try extraction anyway)")
            
            # ─────────────────────────────────────────────────────────
            # STEP 6: Extract judgment content via JavaScript
            # ─────────────────────────────────────────────────────────
            logger.info(f"   📖 Extracting judgment text...")
            judgment_data = await self._page.evaluate("""
                () => {
                    // Check for auth/login page
                    const pageText = document.body.innerText.toLowerCase();
                    const isLoginPage = pageText.includes('please enter a valid id') ||
                                       (pageText.includes('sign in') && pageText.includes('password')) ||
                                       (pageText.includes('log in') && pageText.includes('username'));
                    
                    if (isLoginPage) {
                        return {
                            success: false,
                            error: "Document page requires authentication",
                            page_title: document.title || "Unknown"
                        };
                    }
                    
                    // Extract document content - try multiple selectors
                    const selectors = [
                        '[data-cy="document-content"]',
                        '#documentcontent',
                        '#api_content',
                        '.document-content-wrapper',
                        '.ss-document-content',
                        'main article',
                        'main',
                        'article',
                        '.content-area'
                    ];
                    
                    let fullText = "";
                    
                    for (const selector of selectors) {
                        const elem = document.querySelector(selector);
                        if (elem) {
                            const text = (elem.innerText || elem.textContent || "").trim();
                            if (text.length > 200) {
                                fullText = text;
                                break;
                            }
                        }
                    }
                    
                    // Fallback: get body text if nothing else works
                    if (!fullText || fullText.length < 200) {
                        fullText = document.body.innerText || "";
                    }
                    
                    const wordCount = fullText.split(/\\s+/).filter(w => w.length > 0).length;
                    
                    // Extract headnotes if present
                    let headnotes = "";
                    const hnEl = document.querySelector('.headnotes, [data-cy="headnotes"]');
                    if (hnEl) headnotes = (hnEl.innerText || "").trim();
                    
                    // Detect embedded links that point to the REAL full document
                    // These appear when the current page only shows a summary/headnote
                    const embeddedLinks = Array.from(document.querySelectorAll('a.SS_EmbeddedLink[data-docfullpath]'));
                    const embeddedLinkInfo = embeddedLinks.map(a => ({
                        docfullpath: a.getAttribute('data-docfullpath') || '',
                        title: a.getAttribute('title') || '',
                        text: (a.innerText || a.textContent || '').trim(),
                        contentcomponentid: a.getAttribute('data-contentcomponentid') || '',
                    })).filter(l => l.docfullpath && l.docfullpath.includes('/shared/document/'));
                    
                    if (!fullText || fullText.trim().length < 100) {
                        return {
                            success: false,
                            error: "Could not extract document content (too short or empty)",
                            page_title: document.title || "Unknown",
                            page_url: window.location.href,
                            embedded_links: embeddedLinkInfo
                        };
                    }
                    
                    return {
                        success: true,
                        full_text: fullText.trim(),
                        word_count: wordCount,
                        headnotes: headnotes,
                        page_title: document.title || "Unknown",
                        page_url: window.location.href,
                        embedded_links: embeddedLinkInfo
                    };
                }
            """)
            
            # ─────────────────────────────────────────────────────────
            # STEP 6.5: Follow embedded link if content is insufficient
            # When a case page only shows a summary, it contains 
            # <a class="SS_EmbeddedLink" data-docfullpath="..."> 
            # that links to the full judgment document.
            # ─────────────────────────────────────────────────────────
            embedded_links = judgment_data.get("embedded_links", []) if judgment_data else []
            content_is_thin = (
                not judgment_data or 
                not judgment_data.get("success") or 
                (judgment_data.get("word_count", 0) < 500 and len(embedded_links) > 0)
            )
            
            if content_is_thin and embedded_links:
                logger.info(f"   🔗 Content is thin ({judgment_data.get('word_count', 0)} words) — found {len(embedded_links)} embedded link(s), following first one...")
                
                best_link = embedded_links[0]
                docpath = best_link.get("docfullpath", "")
                link_text = best_link.get("text", "")
                logger.info(f"   🔗 Embedded link: {link_text} → {docpath[:80]}...")
                
                try:
                    # Click the embedded link using its data-docfullpath attribute
                    clicked_embedded = False
                    
                    # Method 1: Click the exact embedded link element
                    try:
                        embedded_el = await self._page.wait_for_selector(
                            f'a.SS_EmbeddedLink[data-docfullpath="{docpath}"]',
                            timeout=5000,
                            state="visible"
                        )
                        if embedded_el:
                            await embedded_el.click()
                            clicked_embedded = True
                            logger.info(f"   ✅ Clicked embedded link element")
                    except Exception as click_err:
                        logger.debug(f"   Direct click failed: {click_err}")
                    
                    # Method 2: Use JavaScript to trigger the Lexis getDocument function
                    if not clicked_embedded:
                        try:
                            await self._page.evaluate(f"""
                                () => {{
                                    const link = document.querySelector('a.SS_EmbeddedLink[data-docfullpath="{docpath}"]');
                                    if (link) {{
                                        link.click();
                                        return true;
                                    }}
                                    return false;
                                }}
                            """)
                            clicked_embedded = True
                            logger.info(f"   ✅ Triggered embedded link via JS click")
                        except Exception as js_err:
                            logger.debug(f"   JS click failed: {js_err}")
                    
                    # Method 3: Navigate directly using the docfullpath to construct URL
                    if not clicked_embedded:
                        try:
                            # Construct the document URL from the docfullpath
                            # e.g., /shared/document/cases-my/urn:contentItem:XXX → full Lexis URL
                            doc_url = f"https://advance.lexis.com/document?pddocfullpath={docpath}&pdmfid=1522468"
                            logger.info(f"   🔗 Navigating directly to: {doc_url[:80]}...")
                            await self._page.goto(doc_url, timeout=30000, wait_until="domcontentloaded")
                            clicked_embedded = True
                            logger.info(f"   ✅ Direct navigation to embedded document")
                        except Exception as nav_err:
                            logger.warning(f"   ⚠️ Direct navigation failed: {nav_err}")
                    
                    if clicked_embedded:
                        # Wait for the full document to load
                        await asyncio.sleep(2)
                        try:
                            await self._page.wait_for_load_state("domcontentloaded", timeout=15000)
                        except:
                            pass
                        
                        try:
                            await self._page.wait_for_selector(
                                '[data-cy="document-content"], #documentcontent, .document-content-wrapper, #api_content',
                                timeout=10000
                            )
                            logger.info(f"   ✅ Full document content loaded")
                        except:
                            logger.debug(f"   Document content selector timeout after embedded link")
                        
                        await asyncio.sleep(1)
                        
                        # Re-extract content from the REAL full document page
                        logger.info(f"   📖 Re-extracting from full document...")
                        full_judgment_data = await self._page.evaluate("""
                            () => {
                                const selectors = [
                                    '[data-cy="document-content"]',
                                    '#documentcontent',
                                    '#api_content',
                                    '.document-content-wrapper',
                                    '.ss-document-content',
                                    'main article',
                                    'main',
                                    'article',
                                    '.content-area'
                                ];
                                
                                let fullText = "";
                                for (const selector of selectors) {
                                    const elem = document.querySelector(selector);
                                    if (elem) {
                                        const text = (elem.innerText || elem.textContent || "").trim();
                                        if (text.length > 200) {
                                            fullText = text;
                                            break;
                                        }
                                    }
                                }
                                
                                if (!fullText || fullText.length < 200) {
                                    fullText = document.body.innerText || "";
                                }
                                
                                const wordCount = fullText.split(/\\s+/).filter(w => w.length > 0).length;
                                
                                let headnotes = "";
                                const hnEl = document.querySelector('.headnotes, [data-cy="headnotes"]');
                                if (hnEl) headnotes = (hnEl.innerText || "").trim();
                                
                                // Extract sections
                                let judges = "";
                                const judgeEl = document.querySelector('.judges, .judge-name, [data-cy="judges"]');
                                if (judgeEl) judges = (judgeEl.innerText || "").trim();
                                
                                let facts = "";
                                const factsEl = document.querySelector('.facts, [data-cy="facts"]');
                                if (factsEl) facts = (factsEl.innerText || "").trim();
                                
                                return {
                                    success: wordCount > 50,
                                    full_text: fullText.trim(),
                                    word_count: wordCount,
                                    headnotes: headnotes,
                                    judges: judges,
                                    facts: facts,
                                    page_title: document.title || "Unknown",
                                    page_url: window.location.href,
                                    via_embedded_link: true
                                };
                            }
                        """)
                        
                        if full_judgment_data and full_judgment_data.get("success"):
                            old_wc = judgment_data.get("word_count", 0) if judgment_data else 0
                            new_wc = full_judgment_data.get("word_count", 0)
                            logger.info(f"   ✅ Embedded link extraction: {old_wc} → {new_wc} words")
                            judgment_data = full_judgment_data
                        else:
                            logger.warning(f"   ⚠️ Embedded link page extraction also failed")
                    
                except Exception as embed_err:
                    logger.warning(f"   ⚠️ Embedded link follow failed: {embed_err}")
            elif embedded_links and judgment_data and judgment_data.get("success"):
                logger.info(f"   ℹ️ Content OK ({judgment_data.get('word_count', 0)} words) — {len(embedded_links)} embedded link(s) available but not needed")
            
            # ─────────────────────────────────────────────────────────
            # STEP 7: Go BACK to search page for next citation
            # If we followed an embedded link, we need extra go_back
            # ─────────────────────────────────────────────────────────
            followed_embedded = judgment_data.get("via_embedded_link", False) if judgment_data else False
            
            try:
                # First go_back (from document/embedded doc → previous page)
                await self._page.go_back(timeout=10000)
                await asyncio.sleep(1)
                logger.info(f"   ↩️ Navigated back (now at: {self._page.url[:60]}...)")
                
                # If we followed an embedded link, we need another go_back
                # (embedded doc → original doc → search results)
                curr = self._page.url
                if followed_embedded or "/document" in curr or "pddocfullpath" in curr:
                    await self._page.go_back(timeout=10000)
                    await asyncio.sleep(1)
                    logger.info(f"   ↩️ Second back (now at: {self._page.url[:60]}...)")
                
                # If still on a document page, try one more time
                curr = self._page.url
                if "/document" in curr or "pddocfullpath" in curr:
                    await self._page.go_back(timeout=10000)
                    await asyncio.sleep(1)
                    logger.info(f"   ↩️ Third back (now at: {self._page.url[:60]}...)")
            except Exception as back_err:
                logger.warning(f"   ⚠️ go_back() failed: {back_err} (will try to continue)")
            
            # Process result
            if judgment_data and judgment_data.get("success"):
                logger.info(f"   ✅ SUCCESS: {judgment_data.get('word_count', 0):,} words extracted")
                judgment_data['from_cache'] = False
                judgment_data['fetched_by'] = 'citation'
                return judgment_data
            else:
                error = judgment_data.get("error", "Unknown error") if judgment_data else "No data returned"
                logger.warning(f"   ⚠️ FAILED: {error}")
                return {
                    "success": False,
                    "error": error,
                    "full_text": "",
                    "word_count": 0
                }
        
        except Exception as e:
            logger.error(f"❌ Citation fetch error for {citation}: {str(e)}")
            # Try to go back even on error so page stays usable
            try:
                if self._page and not self._page.is_closed():
                    await self._page.go_back(timeout=5000)
                    await asyncio.sleep(0.5)
            except:
                pass
            return {
                "success": False,
                "error": str(e),
                "full_text": "",
                "word_count": 0
            }
    
    async def fetch_full_judgment(self, case_link: str, case_title: str = "") -> Dict[str, Any]:
        """
        Navigate to case document page and extract complete judgment text.
        
        Phase 3: Now checks cache first for instant retrieval (0s vs 3-5s).
        
        Args:
            case_link: Full URL to the case document
            case_title: Optional case title for logging
            
        Returns:
            Dictionary containing:
            - full_text: Complete judgment text (50-200 pages)
            - headnotes: Legal principles summary
            - facts: Detailed facts section (if identifiable)
            - reasoning: Judge's analysis (if identifiable)
            - conclusion: Judgment conclusion (if identifiable)
            - judges: List of judge names
            - word_count: Total words in judgment
            - sections: Any identified section headings
            - success: Boolean indicating if fetch succeeded
            - error: Error message if failed
            - from_cache: Boolean indicating if retrieved from cache
        """
        try:
            # Phase 3: Check cache FIRST
            if self._cache_service:
                cached = self._cache_service.get_cached_judgment(case_link)
                if cached:
                    logger.info(f"⚡ Cache HIT: {case_title or case_link[:60]} ({cached.get('word_count', 0):,} words)")
                    return cached
            
            logger.info(f"📄 Fetching full judgment: {case_title or case_link}")
            
            # Defensive check: Verify browser is still open
            page_is_valid = False
            try:
                page_is_valid = self._page and not self._page.is_closed()
            except Exception as check_error:
                logger.debug(f"Could not check page status: {check_error}")
                page_is_valid = False
            
            if not page_is_valid:
                logger.warning("⚠️ Browser page is not valid, restarting...")
                try:
                    await self.start_robot()
                    if not self._page:
                        raise Exception("Failed to restart browser - page is still None")
                except Exception as restart_error:
                    logger.error(f"❌ Could not restart browser: {restart_error}")
                    return {
                        "success": False,
                        "error": f"Browser unavailable and restart failed: {str(restart_error)}",
                        "full_text": "",
                        "word_count": 0
                    }
            
            # Navigate to the case document
            try:
                await self._page.goto(case_link, timeout=30000, wait_until="domcontentloaded")
                await self._page.wait_for_load_state("networkidle", timeout=15000)
            except Exception as nav_error:
                # Check if browser closed during navigation
                if "closed" in str(nav_error).lower():
                    logger.warning("⚠️ Browser closed during navigation, attempting recovery...")
                    await self.start_robot()
                    await self._page.goto(case_link, timeout=30000, wait_until="domcontentloaded")
                    await self._page.wait_for_load_state("networkidle", timeout=15000)
                else:
                    raise
            
            logger.info(f"✅ Page loaded: {self._page.url}")
            
            # Check if we landed on an intermediate authentication or preview page
            # DISABLED: Button clicking was causing browser context to close
            # The real issue is authentication/session, not intermediate buttons
            # try:
            #     # Common button texts that indicate we need to proceed
            #     button_selectors = [
            #         'button:has-text("View Document")',
            #         'button:has-text("Continue")',
            #         'a:has-text("View Full Text")',
            #     ]
            #     
            #     for selector in button_selectors:
            #         try:
            #             button = await self._page.query_selector(selector)
            #             if button and await button.is_visible():
            #                 logger.info(f"📋 Found intermediate button: {selector} - clicking...")
            #                 await button.click()
            #                 await self._page.wait_for_load_state("networkidle", timeout=10000)
            #                 logger.info(f"✅ Clicked through to document: {self._page.url}")
            #                 break
            #         except Exception as btn_err:
            #             logger.debug(f"Button click failed: {btn_err}")
            #             continue
            # except Exception as e:
            #     logger.debug(f"Button detection skipped: {e}")
            
            # Extract full document content using JavaScript
            try:
                judgment_data = await self._page.evaluate("""
                () => {
                    // First, check if we're on a login/authentication page
                    const pageText = document.body.innerText.toLowerCase();
                    const isLoginPage = pageText.includes('please enter a valid id') ||
                                       pageText.includes('sign in') ||
                                       pageText.includes('log in') ||
                                       pageText.includes('you must accept these terms') ||
                                       (pageText.includes('password') && pageText.includes('username')) ||
                                       document.querySelector('input[type="password"]');
                    
                    if (isLoginPage) {
                        return {
                            success: false,
                            error: "Landed on authentication page - session may have expired",
                            page_title: document.title || "Unknown",
                            url: window.location.href,
                            page_text_sample: document.body.innerText.substring(0, 500)
                        };
                    }
                    
                    // Try multiple selectors for Lexis Advance content containers
                    const selectors = [
                        // Lexis Advance specific selectors
                        '[data-cy="document-content"]',
                        '[data-testid="document-content"]',
                        '.document-content-wrapper',
                        '#documentcontent',
                        '.lni-document-content',
                        
                        // Generic document selectors
                        '#api_content',
                        '.document-view',
                        '.doc-content',
                        '[data-type="document"]',
                        '.document-body',
                        '.document-wrapper',
                        'div[role="document"]',
                        'main',
                        'article'
                    ];
                    
                    let mainContent = null;
                    let fullText = "";
                    
                    // Try specific selectors first
                    for (const selector of selectors) {
                        const elem = document.querySelector(selector);
                        if (elem) {
                            const text = elem.innerText || elem.textContent || "";
                            if (text.trim().length > 100) {
                                mainContent = elem;
                                fullText = text;
                                break;
                            }
                        }
                    }
                    
                    // Fallback: Get all visible text from body, excluding navigation/menus
                    if (!mainContent || fullText.trim().length < 100) {
                        // Remove script, style, nav, header, footer elements
                        const clone = document.body.cloneNode(true);
                        clone.querySelectorAll('script, style, nav, header, footer, [role="navigation"]').forEach(el => el.remove());
                        fullText = clone.innerText || clone.textContent || "";
                        
                        if (fullText.trim().length > 100) {
                            mainContent = document.body;
                        }
                    }
                    
                    if (!mainContent || !fullText || fullText.trim().length < 100) {
                        return {
                            success: false,
                            error: "Could not find main content container on page",
                            page_title: document.title || "Unknown",
                            url: window.location.href,
                            body_length: document.body?.innerText?.length || 0,
                            tried_selectors: selectors.length
                        };
                    }
                    
                    // Clean up text
                    fullText = fullText.trim();
                    
                    // Try to extract structured sections
                    const result = {
                        full_text: fullText,
                        success: true
                    };
                    
                    // Extract headnotes (usually at top)
                    const headnotesEl = document.querySelector('.headnotes, [data-section="headnotes"], .catchwords');
                    if (headnotesEl) {
                        result.headnotes = headnotesEl.innerText || headnotesEl.textContent || "";
                    }
                    
                    // Try to identify facts section - use RegExp constructor to avoid escaping issues
                    const factsPattern = new RegExp('(?:FACTS?|BACKGROUND)[\\s:]*\\n([\\s\\S]{100,}?)(?:\\n(?:ISSUES?|HELD|JUDGMENT|DECISION|GROUNDS?)[\\s:]*\\n|$)', 'i');
                    const factsMatch = fullText.match(factsPattern);
                    if (factsMatch && factsMatch[1]) {
                        result.facts = factsMatch[1].trim().substring(0, 5000); // Limit to 5000 chars
                    }
                    
                    // Try to identify issues section
                    const issuesPattern = new RegExp('(?:ISSUES?|QUESTIONS?)[\\s:]*\\n([\\s\\S]{50,}?)(?:\\n(?:HELD|JUDGMENT|DECISION|GROUNDS?)[\\s:]*\\n|$)', 'i');
                    const issuesMatch = fullText.match(issuesPattern);
                    if (issuesMatch && issuesMatch[1]) {
                        result.issues_text = issuesMatch[1].trim().substring(0, 3000);
                    }
                    
                    // Try to identify judgment/reasoning section
                    const reasoningPattern = new RegExp('(?:JUDGMENT|GROUNDS? OF (?:DECISION|JUDGMENT)|DECISION)[\\s:]*\\n([\\s\\S]{200,}?)(?:\\n(?:CONCLUSION|ORDER|DATED)[\\s:]*|$)', 'i');
                    const reasoningMatch = fullText.match(reasoningPattern);
                    if (reasoningMatch && reasoningMatch[1]) {
                        result.reasoning = reasoningMatch[1].trim().substring(0, 20000); // Limit to 20000 chars
                    }
                    
                    // Try to find judge names
                    const judges = [];
                    const judgeEls = document.querySelectorAll('.judge-name, [data-field="judge"], .coram');
                    judgeEls.forEach(el => {
                        const text = (el.innerText || el.textContent || "").trim();
                        if (text && text.length < 100) {
                            judges.push(text);
                        }
                    });
                    
                    // Also try regex for judge names in CORAM section
                    const coramPattern = new RegExp('CORAM[\\s:]*\\n([^\\n]+)', 'i');
                    const coramMatch = fullText.match(coramPattern);
                    if (coramMatch && coramMatch[1]) {
                        judges.push(coramMatch[1].trim());
                    }
                    
                    if (judges.length > 0) {
                        result.judges = judges;
                    }
                    
                    // Extract any section headings (for structure awareness)
                    const headings = [];
                    document.querySelectorAll('h1, h2, h3, h4, .section-heading').forEach(h => {
                        const heading = (h.innerText || h.textContent || "").trim();
                        if (heading && heading.length < 200 && heading.length > 3) {
                            headings.push(heading);
                        }
                    });
                    if (headings.length > 0) {
                        result.sections = headings.slice(0, 50); // Max 50 headings
                    }
                    
                    // Calculate word count
                    result.word_count = fullText.split(/\s+/).filter(w => w.length > 0).length;
                    
                    return result;
                }
            """)
            except Exception as eval_error:
                if "closed" in str(eval_error).lower():
                    logger.error(f"❌ Browser closed during content extraction: {eval_error}")
                    return {
                        "success": False,
                        "error": f"Browser closed unexpectedly during extraction: {str(eval_error)}",
                        "full_text": "",
                        "word_count": 0
                    }
                else:
                    raise  # Re-raise if it's not a "closed" error
            
            if not judgment_data or not judgment_data.get("success"):
                error_msg = judgment_data.get("error", "Unknown error") if judgment_data else "No data returned"
                logger.warning(f"⚠️ Failed to extract judgment: {error_msg}")
                
                # Save debug capture to analyze what page we actually landed on
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_title = "".join(c for c in case_title[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
                    
                    # Save screenshot
                    screenshot_path = self.debug_dir / f"failed_extraction_{safe_title}_{timestamp}.png"
                    await self._page.screenshot(path=str(screenshot_path), full_page=True)
                    logger.info(f"📸 Debug screenshot saved: {screenshot_path}")
                    
                    # Save HTML
                    html_path = self.debug_dir / f"failed_extraction_{safe_title}_{timestamp}.html"
                    html_content = await self._page.content()
                    html_path.write_text(html_content, encoding='utf-8')
                    logger.info(f"📄 Debug HTML saved: {html_path}")
                    
                    # Add debug info to error
                    if judgment_data:
                        judgment_data['debug_screenshot'] = str(screenshot_path)
                        judgment_data['debug_html'] = str(html_path)
                    
                except Exception as debug_error:
                    logger.debug(f"Could not save debug capture: {debug_error}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "full_text": "",
                    "word_count": 0,
                    "page_url": self._page.url if self._page else case_link,
                    "page_title": judgment_data.get("page_title", "Unknown") if judgment_data else "Unknown"
                }
            
            word_count = judgment_data.get("word_count", 0)
            logger.info(f"✅ Extracted judgment: {word_count:,} words")
            
            # Log section availability
            sections_found = []
            if judgment_data.get("headnotes"): sections_found.append("headnotes")
            if judgment_data.get("facts"): sections_found.append("facts")
            if judgment_data.get("issues_text"): sections_found.append("issues")
            if judgment_data.get("reasoning"): sections_found.append("reasoning")
            if judgment_data.get("judges"): sections_found.append("judges")
            
            if sections_found:
                logger.info(f"📋 Sections identified: {', '.join(sections_found)}")
            
            # Phase 3: Store in cache for next time
            if self._cache_service and judgment_data.get("success"):
                try:
                    judgment_data_with_title = judgment_data.copy()
                    judgment_data_with_title['title'] = case_title
                    self._cache_service.store_judgment(case_link, judgment_data_with_title)
                    logger.info(f"💾 Cached for future use")
                except Exception as cache_error:
                    logger.warning(f"⚠️ Failed to cache judgment: {cache_error}")
            
            judgment_data['from_cache'] = False
            return judgment_data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch judgment for {case_title}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "full_text": "",
                "word_count": 0
            }
    
    async def fetch_multiple_judgments(self, cases: List[Dict[str, Any]], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """
        OPTION B: Fetch full judgments using CITATION SEARCH only.
        
        Assumes self._page is already on an authenticated Lexis search page.
        Uses fetch_judgment_by_citation() for every case (no URL navigation).
        Never calls page.goto() - uses search box for each citation.
        
        Args:
            cases: List of case dictionaries with 'citation' field
            max_concurrent: Unused (sequential for stability)
            
        Returns:
            List of cases enriched with full judgment data
        """
        logger.info(f"📚 OPTION B: Citation-based batch fetch for {len(cases)} cases")
        logger.info(f"⏰ Browser timeout: {self.timeout/60000:.1f} minutes")
        
        # Verify browser page is alive and on Lexis
        if not self._page or self._page.is_closed():
            logger.error(f"❌ Browser page is not available!")
            for case in cases:
                case["full_judgment_fetched"] = False
                case["full_judgment_error"] = "Browser page not available"
            return cases
        
        current_url = self._page.url
        logger.info(f"📄 Starting page: {current_url}")
        
        if "advance.lexis.com" not in current_url:
            logger.error(f"❌ Not on Lexis page! Current URL: {current_url}")
            for case in cases:
                case["full_judgment_fetched"] = False
                case["full_judgment_error"] = "Not on Lexis page"
            return cases
        
        enriched_cases = []
        fetched_count = 0
        error_count = 0
        skip_count = 0
        total_words = 0
        
        for i, case in enumerate(cases, 1):
            case_citation = case.get("citation", "No Citation")
            case_title = case.get("title", f"Case {i}")
            
            # Skip cases without citation
            if not case_citation or case_citation == "No Citation":
                logger.warning(f"[{i}/{len(cases)}] No citation, skipping: {case_title[:50]}")
                case["full_judgment_fetched"] = False
                case["full_judgment_error"] = "No citation available for search"
                skip_count += 1
                enriched_cases.append(case)
                continue
            
            # Check if browser is still alive
            if self._page.is_closed():
                logger.error(f"❌ Browser page closed at case {i}/{len(cases)}!")
                for remaining_case in cases[i-1:]:
                    remaining_case["full_judgment_fetched"] = False
                    remaining_case["full_judgment_error"] = "Browser closed during batch fetch"
                    enriched_cases.append(remaining_case)
                break
            
            logger.info(f"[{i}/{len(cases)}] Fetching: {case_title[:60]}...")
            logger.info(f"   Citation: {case_citation}")
            
            # Use citation-based fetch ONLY (no URL fallback = no browser crashes)
            judgment_data = await self.fetch_judgment_by_citation(case_citation, case_title)
            
            if judgment_data and judgment_data.get("success"):
                case["full_judgment"] = judgment_data.get("full_text", "")
                case["judgment_word_count"] = judgment_data.get("word_count", 0)
                case["judgment_headnotes"] = judgment_data.get("headnotes", "")
                case["judgment_facts"] = judgment_data.get("facts", "")
                case["judgment_issues"] = judgment_data.get("issues_text", "")
                case["judgment_reasoning"] = judgment_data.get("reasoning", "")
                case["judgment_judges"] = judgment_data.get("judges", [])
                case["judgment_sections"] = judgment_data.get("sections", [])
                case["full_judgment_fetched"] = True
                case["from_cache"] = False
                
                fetched_count += 1
                total_words += judgment_data.get("word_count", 0)
                
                logger.info(f"   SUCCESS: {judgment_data.get('word_count', 0):,} words extracted")
            else:
                error_msg = judgment_data.get("error", "Unknown error") if judgment_data else "No data"
                case["full_judgment_fetched"] = False
                case["full_judgment_error"] = error_msg
                error_count += 1
                logger.warning(f"   FAILED: {error_msg}")
            
            enriched_cases.append(case)
            
            # Keep-alive: Log session status every 5 cases
            if i % 5 == 0 and i < len(cases):
                try:
                    if self._page and not self._page.is_closed():
                        logger.info(f"Keep-alive [{i}/{len(cases)}]: Page at {self._page.url[:60]}...")
                    else:
                        logger.warning(f"Keep-alive [{i}/{len(cases)}]: Page is CLOSED!")
                except Exception as ka_error:
                    logger.warning(f"Keep-alive check error: {ka_error}")
            
            # Delay between fetches
            if i < len(cases):
                await asyncio.sleep(1)
        
        logger.info(f"OPTION B COMPLETE: {fetched_count} success, {error_count} failed, {skip_count} skipped out of {len(cases)} total. {total_words:,} words extracted.")
        
        return enriched_cases
