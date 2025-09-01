from playwright.async_api import async_playwright, Browser
from typing import Optional, Dict, Any
import logging
from datetime import datetime
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
    
    async def extract_work_order_data(self, url: str, custom_selectors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Spezielle Extraktion für Auftragsdaten mit intelligenter Felderkennung
        
        Args:
            url: Die URL der Auftragsseite
            custom_selectors: Optional - spezifische CSS-Selektoren für bekannte Websites
        """
        if not self.browser:
            raise RuntimeError("Playwright browser not initialized")
        
        page = await self.browser.new_page()
        try:
            await page.goto(url, timeout=settings.playwright_timeout)
            
            # Basis-Informationen sammeln
            result = {
                "url": url,
                "title": await page.title(),
                "extraction_timestamp": datetime.now().isoformat()
            }
            
            # Verwende custom selectors falls vorhanden
            if custom_selectors:
                logger.info("Using custom selectors for work order extraction")
                for field_name, selector in custom_selectors.items():
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            result[field_name] = await element.inner_text()
                        else:
                            logger.warning(f"Selector '{selector}' for field '{field_name}' found no elements")
                    except Exception as e:
                        logger.warning(f"Failed to extract field '{field_name}' with selector '{selector}': {e}")
            
            else:
                # Intelligente automatische Extraktion
                logger.info("Using intelligent automatic extraction")
                
                # JavaScript für intelligente Extraktion ausführen
                extracted_data = await page.evaluate("""
                    () => {
                        const data = {};
                        
                        // Suche nach Problem-/Schadensbeschreibung
                        const problemSelectors = [
                            '[class*="problem"]', '[class*="beschreibung"]', '[class*="schaden"]',
                            '[class*="meldung"]', '[class*="info"]', '[id*="problem"]', 
                            '[id*="beschreibung"]', 'textarea', '.description'
                        ];
                        
                        for (let selector of problemSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.innerText.trim().length > 10) {
                                data.problem_description = element.innerText.trim();
                                break;
                            }
                        }
                        
                        // Suche nach Auftragsnummer/Bestellnummer
                        const orderSelectors = [
                            '[class*="order"]', '[class*="auftrag"]', '[class*="bestell"]',
                            '[class*="referenz"]', '[id*="order"]', '[id*="nummer"]'
                        ];
                        
                        for (let selector of orderSelectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                const text = element.innerText.trim();
                                const numberMatch = text.match(/[A-Z]?\\d{6,}/);
                                if (numberMatch) {
                                    data.order_number = numberMatch[0];
                                    break;
                                }
                            }
                        }
                        
                        // Suche nach Termininformationen
                        const dateSelectors = [
                            '[class*="termin"]', '[class*="date"]', '[class*="datum"]',
                            'input[type="date"]', '[id*="termin"]', '[id*="date"]'
                        ];
                        
                        for (let selector of dateSelectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                const text = element.innerText || element.value || '';
                                const dateMatch = text.match(/\\d{1,2}\\.\\d{1,2}\\.\\d{4}|\\d{4}-\\d{2}-\\d{2}/);
                                if (dateMatch) {
                                    data.appointment_date = dateMatch[0];
                                    break;
                                }
                            }
                        }
                        
                        // Suche nach Zeitangaben
                        const timeSelectors = [
                            '[class*="zeit"]', '[class*="time"]', '[class*="uhr"]',
                            'input[type="time"]', '[id*="zeit"]', '[id*="time"]'
                        ];
                        
                        for (let selector of timeSelectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                const text = element.innerText || element.value || '';
                                const timeMatch = text.match(/\\d{1,2}:\\d{2}.*?\\d{1,2}:\\d{2}|\\d{1,2}:\\d{2}/);
                                if (timeMatch) {
                                    data.appointment_time = timeMatch[0];
                                    break;
                                }
                            }
                        }
                        
                        // Suche nach Standort/Objekt
                        const locationSelectors = [
                            '[class*="standort"]', '[class*="objekt"]', '[class*="location"]',
                            '[class*="adresse"]', '[id*="standort"]', '[id*="objekt"]'
                        ];
                        
                        for (let selector of locationSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.innerText.trim().length > 5) {
                                data.location_name = element.innerText.trim();
                                break;
                            }
                        }
                        
                        // Suche nach Kontaktperson
                        const contactSelectors = [
                            '[class*="kontakt"]', '[class*="ansprech"]', '[class*="meldender"]',
                            '[class*="contact"]', '[id*="kontakt"]', '[id*="contact"]'
                        ];
                        
                        for (let selector of contactSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.innerText.trim().length > 3) {
                                data.contact_person = element.innerText.trim();
                                break;
                            }
                        }
                        
                        // Suche nach Telefonnummer
                        const phonePattern = /\\+?[\\d\\s\\-\\(\\)]{8,}/;
                        const allText = document.body.innerText;
                        const phoneMatch = allText.match(phonePattern);
                        if (phoneMatch) {
                            data.contact_phone = phoneMatch[0].trim();
                        }
                        
                        // Sammle alle Tabellendaten (oft enthalten strukturierte Informationen)
                        const tables = document.querySelectorAll('table');
                        if (tables.length > 0) {
                            data.table_data = [];
                            tables.forEach((table, index) => {
                                if (index < 3) { // Nur erste 3 Tabellen
                                    const rows = [];
                                    table.querySelectorAll('tr').forEach(row => {
                                        const cells = [];
                                        row.querySelectorAll('td, th').forEach(cell => {
                                            cells.push(cell.innerText.trim());
                                        });
                                        if (cells.length > 0) rows.push(cells);
                                    });
                                    if (rows.length > 0) data.table_data.push(rows);
                                }
                            });
                        }
                        
                        return data;
                    }
                """)
                
                result.update(extracted_data)
            
            # Zusätzliche Metadaten extrahieren
            result["page_html"] = await page.content()  # Vollständiges HTML für weitere Verarbeitung
            result["extraction_method"] = "custom" if custom_selectors else "intelligent"
            
            logger.info(f"Extracted work order data from {url}: {list(result.keys())}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract work order data from {url}: {e}")
            raise
        finally:
            await page.close()
    
    async def extract_with_smart_detection(self, url: str) -> Dict[str, Any]:
        """
        Intelligente Extraktion die versucht, die Website-Struktur zu erkennen
        und entsprechende Extraktionsstrategien anzuwenden
        """
        if not self.browser:
            raise RuntimeError("Playwright browser not initialized")
        
        page = await self.browser.new_page()
        try:
            await page.goto(url, timeout=settings.playwright_timeout)
            
            # Website-Typ erkennen
            site_analysis = await page.evaluate("""
                () => {
                    const analysis = {
                        has_forms: document.querySelectorAll('form').length > 0,
                        has_tables: document.querySelectorAll('table').length > 0,
                        has_cms_indicators: false,
                        likely_cms: 'unknown',
                        form_count: document.querySelectorAll('form').length,
                        table_count: document.querySelectorAll('table').length,
                        input_count: document.querySelectorAll('input').length
                    };
                    
                    // CMS-Erkennung
                    const bodyClasses = document.body.className.toLowerCase();
                    const headContent = document.head.innerHTML.toLowerCase();
                    
                    if (bodyClasses.includes('wordpress') || headContent.includes('wp-content')) {
                        analysis.likely_cms = 'wordpress';
                        analysis.has_cms_indicators = true;
                    } else if (bodyClasses.includes('drupal') || headContent.includes('drupal')) {
                        analysis.likely_cms = 'drupal';
                        analysis.has_cms_indicators = true;
                    } else if (headContent.includes('typo3')) {
                        analysis.likely_cms = 'typo3';
                        analysis.has_cms_indicators = true;
                    }
                    
                    return analysis;
                }
            """)
            
            # Basierend auf Analyse entsprechende Extraktion durchführen
            if site_analysis['has_forms'] and site_analysis['input_count'] > 5:
                # Wahrscheinlich ein Formular-System
                return await self.extract_work_order_data(url)
            elif site_analysis['has_tables']:
                # Tabellen-basierte Darstellung
                return await self.extract_from_url(url, {
                    "extract_links": True,
                    "selectors": {
                        "table_content": "table",
                        "main_content": "main, .content, #content"
                    }
                })
            else:
                # Standard-Extraktion
                return await self.extract_work_order_data(url)
                
        finally:
            await page.close()
    
    def is_available(self) -> bool:
        """Check if Playwright browser is available"""
        return self.browser is not None


# Global Playwright service instance
playwright_service = PlaywrightService()
