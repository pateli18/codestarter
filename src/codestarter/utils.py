import asyncio

from pydantic_settings import BaseSettings


class CodeStarterSettings(BaseSettings):
    max_concurrent_ops: int = 100


settings = CodeStarterSettings()

OpsSemaphore = asyncio.Semaphore(settings.max_concurrent_ops)
