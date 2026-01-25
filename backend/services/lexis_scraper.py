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
else:
    Browser = Any = object
    Page = Any = object
    BrowserContext = Any = object
    TimeoutError = Any = object
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
    
    def __init__(self, use_pool: bool = True):
        """Initialize settings from environment."""
        self.username = settings.LEXIS_USERNAME
        self.password = settings.LEXIS_PASSWORD
        self.headless = getattr(settings, "LEXIS_HEADLESS", True)
        self.timeout = 60000  # 60 seconds (extended for login)
        self.use_pool = use_pool  # Use browser pool for performance
        
        # Session storage
        self.session_file = Path("lexis_session.json")
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._pool: Optional[BrowserPool] = None
        
        # Debug captures directory
        self.debug_dir = Path("debug_captures")
        
        if not self.username or not self.password:
             logger.warning("LEXIS_USERNAME or LEXIS_PASSWORD not set. Login will fail.")

    async def start_robot(self):
        """Wake up the robot (Launch browser or get from pool)."""
        if self.use_pool:
            # Use browser pool for performance (saves 5-10 seconds per search)
            logger.info("🚀 Getting browser from pool...")
            self._pool = await BrowserPool.get_instance()
            self._page = await self._pool.get_page()
            logger.info("✅ Got pooled browser page")
            return
        
        # Legacy: Launch new browser each time
        logger.info(f"🤖 Starting Robot Browser (Headless: {self.headless})...")
        from playwright.async_api import async_playwright
        p = await async_playwright().start()
        
        # Launch with stealth settings to bypass bot detection
        self._browser = await p.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
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
            
        self._page = await self._context.new_page()
        
        # Hide webdriver property to avoid bot detection
        await self._page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    async def close_robot(self):
        """Put the robot to sleep (release page back to pool)."""
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
                current_url = self._page.url if self._page else ""
                if any(domain in current_url for domain in self.LEXIS_DOMAINS):
                    storage = await self._context.storage_state()
                    with open(self.session_file, 'w') as f:
                        json.dump(storage, f)
                    logger.info("✅ Session cookies saved (Lexis authentication valid).")
                else:
                    logger.warning("⚠️ Not saving session - not on Lexis domain")
                    # Remove invalid session file if it exists
                    if self.session_file.exists():
                        self.session_file.unlink()
                        logger.info("🗑️ Removed invalid session file")
            except Exception as e:
                logger.error(f"Failed to save session: {e}")
                
        if self._browser:
            await self._browser.close()
            logger.info("🤖 Robot Browser closed.")

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
                timeout=30000
            )
        except Exception:
            pass # Check URL below
            
        current_url = self._page.url
        
        # HANDLE OPENATHENS CHOOSER INTERCEPTION
        if "login.openathens.net" in current_url:
            logger.info("ℹ️ Landed on OpenAthens chooser - selecting 'UM Staff and Students'")
            
            try:
                # Wait for any loader to disappear
                try:
                    await self._page.wait_for_selector(".loader", state="hidden", timeout=10000)
                except:
                    pass

                # Wait for the element
                selector = "div[role='link']:has-text('UM Staff')"
                await self._page.wait_for_selector(selector, timeout=10000)
                
                logger.info("👉 Focusing and pressing Enter on 'UM Staff' option...")
                # Try focus and enter (often works for GWT/Accessible apps)
                await self._page.focus(selector)
                await self._page.keyboard.press("Enter")
                
                # Also try click just in case
                await self._page.click(selector, force=True, timeout=2000)
                
            except Exception as e:
                logger.warning(f"Failed to interact with UM Staff option: {e}")
                # Try clicking the chevron icon explicitly
                try:
                    await self._page.click(".fa-chevron-circle-right", force=True)
                except:
                    pass
            
            # Now wait for redirect to CAS
            logger.info("⏳ Option activated - waiting for redirect to CAS...")
            try:
                await self._page.wait_for_url(lambda u: self.CAS_DOMAIN in u, timeout=15000)
            except Exception:
                pass # Check URL below
        
        current_url = self._page.url
        
        # Now validate where we are
        if self.EZPROXY_DOMAIN in current_url:
             # Loop wait if still on EzProxy
            logger.info("On EzProxy page - waiting for final redirect...")
            try:
                await self._page.wait_for_url(lambda u: self.CAS_DOMAIN in u, timeout=15000)
            except Exception:
                await self._capture_debug_state("step3_ezproxy_stuck")
                raise Exception(f"Stuck on EzProxy page: {current_url}")
        
        current_url = self._page.url
        if not (self.CAS_DOMAIN in current_url or any(d in current_url for d in self.LEXIS_DOMAINS)):
             await self._capture_debug_state("step3_unexpected_redirect")
             raise Exception(
                f"Unexpected redirect destination: {current_url}. "
                "Expected CAS login page or Lexis."
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
                await self._page.wait_for_selector("#login-form", timeout=10000)
                
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
                timeout=60000
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

    async def search(self, query: str, country: str = "Malaysia", filters: Dict = None) -> List[Dict]:
        """
        Execute the search robot with comprehensive filter support.
        """
        if filters is None:
            filters = {}
            
        try:
            search_start = datetime.now()
            # 1. Acquire Page (Persistent or New)
            await self.start_robot()
            
            # =========================================================================
            # OPTIMISTIC SEARCH STRATEGY
            # Attempt to search immediately without verifying session state.
            # If we can find the search box and type, we are logged in.
            # If we fail, we assume session is dead and trigger re-login.
            # =========================================================================
            
            search_selectors = [
                 # High Precision Selectors (from User DOM)
                 ".searchcontainer_desktop textarea",
                 "div.expandingTextarea textarea",
                 "#searchTerms", 
                 "textarea[id='searchTerms']",
                 
                 # Fallbacks
                 "[placeholder*='Enter terms']", 
                 "textarea[name='search']",
                 "input[name='search']",
                 "#mainSearch",
             ]
            
            # Try to find input immediately
            search_input = None
            try:
                # 1.1 If already on Lexis, check visibility first without navigation
                current_url = self._page.url
                
                # Check if we are already on a results page or search page
                is_on_lexis = any(d in current_url for d in self.LEXIS_DOMAINS)
                
                if not is_on_lexis or current_url == "about:blank":
                    logger.info(f"📄 Page at {current_url} - Navigating to Lexis Search...")
                    # Faster timeout for navigation in optimistic mode
                    await self._page.goto("https://advance.lexis.com/search", timeout=20000)
                
                # Try to find search box with a shorter but effective wait
                for selector in search_selectors:
                    try:
                        # Use wait_for_selector with shorter timeout for each
                        element = await self._page.wait_for_selector(selector, timeout=3000, state="visible")
                        if element:
                            search_input = element
                            logger.info(f"⚡ Found search box via: {selector}")
                            break
                    except:
                        continue
                
                if search_input:
                    logger.info("⚡ OPTIMISTIC SEARCH: Found search box immediately! Skipping login flow.")
                else:
                    raise Exception("Search box not visible after optimistic checks")

                    
            except Exception as e:
                # If optimistic check failed, fall back to safe login flow
                logger.info(f"⚠️ Optimistic search failed ({e}). Starting full login flow...")
                await self.login_flow()
                
                # Retry finding search input after login
                for selector in search_selectors:
                    try:
                        element = await self._page.wait_for_selector(selector, timeout=5000)
                        if element:
                            search_input = element
                            break
                    except Exception:
                        continue
            
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
            
            js_payload = """
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
