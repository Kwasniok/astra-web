"""
REST requests to astra-web.


Requires environment variables or `.env` with:
```
ASTRA_WEB_URL=<url to astra-web server>
ASTRA_WEB_API_KEY=<your api key>
```
"""

from typing import Any, Callable
import os
from dotenv import load_dotenv
from datetime import datetime
from aiohttp.client_exceptions import ClientResponseError
from rest_requests import request as rest_request, RequestMethod, JSON, json_diff


load_dotenv()


async def request(
    endpoint: str,
    method: RequestMethod,
    body: JSON | None = None,
    timeout: int = 600,
) -> JSON:
    """
    Make an asynchronous request to the ASTRA web API.
    See `http://<hostname>:<port>/docs` for more detail on the API.

    :param method: RequestMethod
        The HTTP method to be used. Example: RequestMethod.GET
    :param endpoint: str
        The endpoint to be called. Example: "particles"
    :param body: dict[str, Any], default = {}
        The request body.
    :param timeout: int, default = 600
        Request timeout in seconds
    :return: JSON response

    :raises ClientResponseError:
        If the request fails.
    """

    url = os.getenv("ASTRA_WEB_URL")
    if url is None:
        raise ValueError(
            "Environment variable 'ASTRA_WEB_URL' is not set. Please set it to the correct URL."
        )

    api_key = os.getenv("ASTRA_WEB_API_KEY")
    if api_key is None:
        raise ValueError(
            "Environment variable 'ASTRA_WEB_API_KEY' is not set. Please set it to your API key."
        )

    return await rest_request(
        method,
        url=url + endpoint,
        headers={"x-api-key": api_key},
        body=body,
        timeout=timeout,
    )
