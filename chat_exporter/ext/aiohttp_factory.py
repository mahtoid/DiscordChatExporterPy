import aiohttp


class ClientSessionFactory:
    """Factory class to get singleton aiohttp ClientSession instance"""

    _session = None

    @classmethod
    async def create_or_get_session(cls) -> aiohttp.ClientSession:
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession()
        return cls._session

    @classmethod
    async def close_session(cls):
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None
