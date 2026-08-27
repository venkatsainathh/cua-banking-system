from playwright.async_api import Page, Locator
from core.models import MultiTierLocator

class LocatorResolver:
    @staticmethod
    async def resolve(page: Page, target: MultiTierLocator, timeout: float = 3000) -> Locator:
        # Tier 1: Accessibility Tree (Role + Name)
        if target.role and target.accessible_name:
            loc = page.get_by_role(target.role, name=target.accessible_name)
            if await loc.count() > 0:
                return loc.first

        # Tier 2: Text matching
        if target.text_content:
            loc = page.get_by_text(target.text_content, exact=False)
            if await loc.count() > 0:
                return loc.first

        # Tier 3: CSS Fallback
        if target.css_fallback:
            loc = page.locator(target.css_fallback)
            if await loc.count() > 0:
                return loc.first

        # Tier 4: XPath Fallback
        if target.xpath_fallback:
            loc = page.locator(target.xpath_fallback)
            if await loc.count() > 0:
                return loc.first

        raise TimeoutError(f"MultiTierLocator failed to resolve element: {target.model_dump()}")