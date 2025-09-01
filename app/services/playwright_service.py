from playwright.async_api import async_playwright, Browser
from typing import Optional, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class PlaywrightService:
    """Service for managing Playwright browser instances and web automation"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        
    async def start(self):
        """Initialize Playwright and browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=settings.playwright_headless
            )
            logger.info("Playwright browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            # Don't raise the exception to allow the service to start without Playwright
            # The API will still work for non-web-scraping endpoints
            logger.warning("API will continue without Playwright functionality")
            self.browser = None
    
    async def stop(self):
        """Clean up Playwright resources"""
        if self.browser:
            await self.browser.close()
            logger.info("Playwright browser closed")
        if self.playwright:
            await self.playwright.stop()
    
    async def extract_from_url(self, url: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract data from a URL using Playwright"""
        if not self.browser:
            raise RuntimeError("Playwright browser not initialized")
        
        page = await self.browser.new_page()
        try:
            await page.goto(url, timeout=settings.playwright_timeout)
            
            # Default extraction: get page title and text content
            title = await page.title()
            text_content = await page.evaluate("document.body.innerText")
            
            result = {
                "title": title,
                "text_content": text_content[:1000] + "..." if len(text_content) > 1000 else text_content,
                "url": url
            }
            
            # Advanced extraction based on config
            if config and "selectors" in config:
                custom_data = {}
                for key, selector in config["selectors"].items():
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            custom_data[key] = await element.inner_text()
                    except Exception as e:
                        logger.warning(f"Failed to extract selector {selector}: {e}")
                        custom_data[key] = None
                
                result["custom_extractions"] = custom_data
            
            # Extract meta tags if requested
            if config and config.get("extract_meta", False):
                meta_tags = await page.evaluate("""
                    () => {
                        const metas = {};
                        document.querySelectorAll('meta').forEach(meta => {
                            const name = meta.getAttribute('name') || meta.getAttribute('property');
                            const content = meta.getAttribute('content');
                            if (name && content) {
                                metas[name] = content;
                            }
                        });
                        return metas;
                    }
                """)
                result["meta_tags"] = meta_tags
            
            # Extract links if requested
            if config and config.get("extract_links", False):
                links = await page.evaluate("""
                    () => {
                        return Array.from(document.querySelectorAll('a[href]')).map(link => ({
                            text: link.innerText.trim(),
                            href: link.href
                        })).filter(link => link.text && link.href);
                    }
                """)
                result["links"] = links[:50]  # Limit to first 50 links
            
            return result
            
        finally:
            await page.close()
    
    def is_available(self) -> bool:
        """Check if Playwright browser is available"""
        return self.browser is not None


# Global Playwright service instance
playwright_service = PlaywrightService()
