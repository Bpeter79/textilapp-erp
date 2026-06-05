import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from postgrest import SyncPostgrestClient

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

# Trükk: Nem a merev SupabaseClient-et használjuk, hanem a mögötte álló 
# Postgrest klienst, ami az adatbázis műveletekért felel. 
# Ez nem validálja a kulcs formátumát, így tökéletesen elfogadja az új sb_publishable_ kulcsot is!
class CustomSupabaseClient:
    def __init__(self, url: str, key: str):
        # A Supabase REST végpontja a /rest/v1 útvonalon érhető el
        rest_url = f"{url}/rest/v1"
        headers = {
            "apiKey": key,
            "Authorization": f"Bearer {key}"
        }
        self.postgrest = SyncPostgrestClient(rest_url, headers=headers)
    
    def table(self, table_name: str):
        return self.postgrest.from_(table_name)

# Globális kliens létrehozása (a routerekben a supabase.table() ugyanúgy működik majd!)
supabase = CustomSupabaseClient(settings.SUPABASE_URL, settings.SUPABASE_KEY)