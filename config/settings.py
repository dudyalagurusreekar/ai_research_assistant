from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # ==========================
    # Agent
    # ==========================
    MAX_STEPS: int = 3

    # ==========================
    # Search
    # ==========================
    SEARCH_RESULTS: int = 2
    REQUEST_TIMEOUT: int = 10

    # ==========================
    # Web Reader
    # ==========================
    PAGE_CHAR_LIMIT: int = 800

    USER_AGENT: str = (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/137.0 Safari/537.36"
    )

    # ==========================
    # Research
    # ==========================
    MAX_REPORT_SIZE: int = 3500

    # ==========================
    # Logging
    # ==========================
    DEBUG: bool = True


settings = Settings()