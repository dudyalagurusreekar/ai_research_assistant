import pytest
from tools.browser.macro.search_strategies import SearchStrategyCoordinator

class MockBrowser:
    def __init__(self, current_url="about:blank"):
        self.url = current_url
        
    def get_current_url(self):
        class Result:
            success = True
            data = self.url
        return Result()


def test_wikipedia_strategy_from_coordinator():
    browser = MockBrowser("https://en.wikipedia.org/wiki/Main_Page")
    coordinator = SearchStrategyCoordinator(browser)
    
    result = coordinator.execute_search("Large Language Model", scope="current_site")
    
    assert result["action"] == "open_url"
    assert "wikipedia.org" in result["url"]
    assert "search=Large+Language+Model" in result["url"]

def test_github_strategy_from_coordinator():
    browser = MockBrowser("https://github.com/dudyala")
    coordinator = SearchStrategyCoordinator(browser)
    
    result = coordinator.execute_search("machine learning", scope="current_site")
    
    assert result["action"] == "open_url"
    assert "github.com/search" in result["url"]
    assert "q=machine+learning" in result["url"]

def test_external_strategy():
    browser = MockBrowser("https://en.wikipedia.org/wiki/Main_Page")
    coordinator = SearchStrategyCoordinator(browser)
    
    # Request external scope explicitly
    result = coordinator.execute_search("Large Language Model", scope="external")
    
    assert result["action"] == "open_url"
    assert "google.com/search" in result["url"]
    assert "q=Large+Language+Model" in result["url"]

def test_generic_fallback_strategy():
    browser = MockBrowser("https://example.com")
    coordinator = SearchStrategyCoordinator(browser)
    
    result = coordinator.execute_search("query text", scope="current_site")
    
    assert result["action"] == "fill_input"
    assert "selector" in result
    assert result["text"] == "query text\\n"
