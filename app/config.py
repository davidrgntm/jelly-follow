import json
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str

    BASE_URL: str = "https://api.follow.jelly.uz"
    TRACKING_DOMAIN: str = "https://go.jelly.uz"

    GOOGLE_SERVICE_ACCOUNT_JSON_PATH: Optional[str] = None
    GOOGLE_SERVICE_ACCOUNT_JSON: Optional[str] = None
    SPREADSHEET_NAME: str = "Jelly Follow - PROD"

    DEFAULT_TIMEZONE: str = "Asia/Tashkent"
    APP_ENV: str = "production"
    BOOTSTRAP_ON_START: bool = False
    SEED_SUPER_ADMIN_ON_START: bool = False

    SUPER_ADMIN_TELEGRAM_ID: str
    INTERNAL_SECRET: str = "change_this"

    INSTAGRAM_UZ_USERNAME: str = "jelly.uz"
    INSTAGRAM_RU_USERNAME: str = "jelly.ru"
    INSTAGRAM_KG_USERNAME: str = "jelly.kg"
    INSTAGRAM_AZ_USERNAME: str = "jelly.az"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_google_credentials(self) -> dict:
        if self.GOOGLE_SERVICE_ACCOUNT_JSON:
            return json.loads(self.GOOGLE_SERVICE_ACCOUNT_JSON)
        if self.GOOGLE_SERVICE_ACCOUNT_JSON_PATH:
            with open(self.GOOGLE_SERVICE_ACCOUNT_JSON_PATH) as f:
                return json.load(f)
        raise ValueError("Google credentials not configured")

    def get_instagram_links(self, country_code: str) -> dict:
        mapping = {
            "UZ": self.INSTAGRAM_UZ_USERNAME,
            "RU": self.INSTAGRAM_RU_USERNAME,
            "KG": self.INSTAGRAM_KG_USERNAME,
            "AZ": self.INSTAGRAM_AZ_USERNAME,
        }
        username = mapping.get(country_code.upper(), self.INSTAGRAM_UZ_USERNAME)
        return {
            "app_link": f"instagram://user?username={username}",
            "web_link": f"https://www.instagram.com/{username}/",
        }


settings = Settings()
