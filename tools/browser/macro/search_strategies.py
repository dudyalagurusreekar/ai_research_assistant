"""Site-aware and Context-aware Search Strategies.

Implements the Strategy Pattern to execute search queries appropriately
based on the current domain and search scope.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from urllib.parse import urlencode, urlparse

class BaseSearchStrategy(ABC):
    """Abstract base class for search strategies."""
    
    @abstractmethod
    def execute(self, query: str, browser: Any) -> Dict[str, Any]:
        """Execute the search query using this strategy.
        
        Args:
            query (str): The search query.
            browser (Browser): The Browser facade.
            
        Returns:
            Dict[str, Any]: Standardized action dictionary or result.
        """
        pass

class ExternalSearchStrategy(BaseSearchStrategy):
    """Strategy for generic external search (Google via DuckDuckGo, Bing, etc)."""
    
    def execute(self, query: str, browser: Any) -> Dict[str, Any]:
        """Navigate to Google search page directly."""
        params = {"q": query}
        target_url = f"https://www.google.com/search?{urlencode(params)}"
        return {
            "action": "open_url",
            "url": target_url
        }

class WikipediaSearchStrategy(BaseSearchStrategy):
    """Strategy for Wikipedia site search."""
    
    def execute(self, query: str, browser: Any) -> Dict[str, Any]:
        params = {"search": query, "title": "Special:Search", "go": "Go"}
        # Check current language subdomain, default to en
        current_url = "https://en.wikipedia.org"
        try:
            res = browser.get_current_url()
            if res.success and "wikipedia.org" in res.data:
                parsed = urlparse(res.data)
                current_url = f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass
            
        target_url = f"{current_url}/w/index.php?{urlencode(params)}"
        return {
            "action": "open_url",
            "url": target_url
        }

class GitHubSearchStrategy(BaseSearchStrategy):
    """Strategy for GitHub site search."""
    
    def execute(self, query: str, browser: Any) -> Dict[str, Any]:
        params = {"q": query, "type": "repositories"}
        target_url = f"https://github.com/search?{urlencode(params)}"
        return {
            "action": "open_url",
            "url": target_url
        }

class AmazonSearchStrategy(BaseSearchStrategy):
    """Strategy for Amazon site search."""
    
    def execute(self, query: str, browser: Any) -> Dict[str, Any]:
        params = {"k": query}
        current_url = "https://www.amazon.com"
        try:
            res = browser.get_current_url()
            if res.success and "amazon." in res.data:
                parsed = urlparse(res.data)
                current_url = f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass
            
        target_url = f"{current_url}/s?{urlencode(params)}"
        return {
            "action": "open_url",
            "url": target_url
        }

class GenericWebsiteSearchStrategy(BaseSearchStrategy):
    """Fallback strategy that tries to find a search input on the current page."""
    
    def execute(self, query: str, browser: Any) -> Dict[str, Any]:
        # Tries to find common search boxes
        search_selectors = [
            "input[type='search']",
            "input[name='q']",
            "input[name='query']",
            "input[name='search']",
            "input[placeholder*='search' i]",
            "input[aria-label*='search' i]"
        ]
        
        # We can simulate a search by returning an action dictionary for macro engine
        # However, it's better to just return the best guess action. 
        # For simplicity, we just use the first likely selector. 
        # A more robust approach would evaluate all selectors and pick the first visible one,
        # but the macro engine will just try the action.
        return {
            "action": "fill_input",
            "selector": search_selectors[0],
            "text": f"{query}\\n" # type Enter
        }

class SearchStrategyCoordinator:
    """Coordinates search strategies based on scope and domain."""
    
    def __init__(self, browser: Any):
        self.browser = browser
        self.strategies: Dict[str, BaseSearchStrategy] = {
            "wikipedia.org": WikipediaSearchStrategy(),
            "github.com": GitHubSearchStrategy(),
            "amazon": AmazonSearchStrategy(),
        }
        self.generic_strategy = GenericWebsiteSearchStrategy()
        self.external_strategy = ExternalSearchStrategy()

    def get_strategy(self, scope: str, current_url: str) -> BaseSearchStrategy:
        if scope == "external":
            return self.external_strategy
            
        parsed = urlparse(current_url)
        domain = parsed.netloc.lower()
        
        # Check specific domains
        for key, strategy in self.strategies.items():
            if key in domain:
                return strategy
                
        # If scope is current_site but no specific strategy, use generic
        if scope in ("current_site", "current_domain") and domain:
            return self.generic_strategy
            
        # Default fallback
        return self.external_strategy

    def execute_search(self, query: str, scope: str = "current_site", url: Optional[str] = None) -> Dict[str, Any]:
        current_url = url
        if not current_url:
            try:
                res = self.browser.get_current_url()
                if res and res.success:
                    current_url = res.data
            except Exception:
                pass
            
        strategy = self.get_strategy(scope, current_url)
        return strategy.execute(query, self.browser)
