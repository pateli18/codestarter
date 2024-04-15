import asyncio

from pydantic_settings import BaseSettings


class FireStarterSettings(BaseSettings):
    max_concurrent_ops: int = 100


settings = FireStarterSettings()

OpsSemaphore = asyncio.Semaphore(settings.max_concurrent_ops)
