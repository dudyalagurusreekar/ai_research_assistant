"""OAuth 2.0 Integration Handlers for Google and GitHub Social Login."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger("OAuthManager")


class AbstractOAuthHandler(ABC):
    """Abstract interface for OAuth 2.0 providers."""

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        pass

    @abstractmethod
    def exchange_code_for_user_info(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        pass


class GoogleOAuthHandler(AbstractOAuthHandler):
    """Google OAuth 2.0 Provider Handler."""

    def __init__(self, client_id: str = "mock_google_client_id", client_secret: str = "mock_google_secret"):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}&scope=email%20profile&state={state}"

    def exchange_code_for_user_info(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        logger.info(f"Exchanged Google OAuth code: {code[:8]}...")
        return {
            "provider": "google",
            "provider_user_id": f"google_{code[:10]}",
            "email": f"google_user_{code[:6]}@gmail.com",
            "full_name": "Google User",
        }


class GitHubOAuthHandler(AbstractOAuthHandler):
    """GitHub OAuth 2.0 Provider Handler."""

    def __init__(self, client_id: str = "mock_github_client_id", client_secret: str = "mock_github_secret"):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        return f"https://github.com/login/oauth/authorize?client_id={self.client_id}&redirect_uri={redirect_uri}&scope=user:email&state={state}"

    def exchange_code_for_user_info(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        logger.info(f"Exchanged GitHub OAuth code: {code[:8]}...")
        return {
            "provider": "github",
            "provider_user_id": f"github_{code[:10]}",
            "email": f"github_user_{code[:6]}@github.com",
            "full_name": "GitHub User",
        }


class OAuthManager:
    """Manager providing OAuth provider lookup."""

    def __init__(self):
        self.providers: Dict[str, AbstractOAuthHandler] = {
            "google": GoogleOAuthHandler(),
            "github": GitHubOAuthHandler(),
        }

    def get_handler(self, provider_name: str) -> Optional[AbstractOAuthHandler]:
        return self.providers.get(provider_name.lower())


oauth_manager = OAuthManager()
