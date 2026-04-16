import socket
import asyncio
from typing import Optional

import aiohttp
from loguru import logger

_session: Optional[aiohttp.ClientSession] = None


async def init_http_session() -> aiohttp.ClientSession:
    global _session

    if _session is not None and not _session.closed:
        return _session

    timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
    connector = aiohttp.TCPConnector(
        family=socket.AF_INET,
        use_dns_cache=True,
        ttl_dns_cache=300,
        limit=100,
        limit_per_host=30,
    )
    _session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    logger.info("HTTP session initialized with custom settings.")
    return _session


def get_http_session() -> aiohttp.ClientSession:
    if _session is None or _session.closed:
        raise RuntimeError("HTTP session is not initialized. Call init_http_session() first.")
    return _session


async def close_http_session() -> None:
    global _session
    if _session is not None and not _session.closed:
        await _session.close()
    _session = None


async def _retry_with_backoff(
    session: aiohttp.ClientSession,
    url: str,
    method: str = "GET",
    max_retries: int = 3,
    initial_delay: float = 1.0,
    **kwargs
) -> Optional[dict]:
    """
    Make HTTP request with exponential backoff retry logic.
    Returns dict with status and data, or None on all retries exhausted.
    """
    delay = initial_delay
    last_error = None
    
    for attempt in range(max_retries):
        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"status": 200, "data": data}
                elif response.status in (429, 503, 504):  # Rate limit or server error
                    logger.warning(f"Binance returned {response.status}, retrying...")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                        delay *= 2  # Exponential backoff
                    continue
                else:
                    return {"status": response.status, "data": None}
        except asyncio.TimeoutError as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1}/{max_retries} timed out, retrying in {delay}s...")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
        except aiohttp.ClientConnectorError as e:
            last_error = e
            logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}, retrying in {delay}s...")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            return None
    
    logger.error(f"All {max_retries} attempts failed. Last error: {last_error}")
    return None
