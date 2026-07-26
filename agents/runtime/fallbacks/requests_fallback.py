import json
import urllib.request
import urllib.parse
from urllib.error import HTTPError, URLError

class Response:
    """A standard requests-like Response object."""
    def __init__(self, url: str, status_code: int, content: bytes, headers: dict):
        self.url = url
        self.status_code = status_code
        self.content = content
        self.headers = headers

    @property
    def text(self) -> str:
        """Returns the decoded string representation of the response content."""
        return self.content.decode("utf-8", errors="replace")

    def json(self):
        """Deserializes JSON response text into Python objects."""
        return json.loads(self.text)

    def raise_for_status(self):
        """Raises an HTTPError if the response status indicates an error."""
        if self.status_code >= 400:
            raise HTTPError(self.url, self.status_code, f"HTTP Error {self.status_code}", self.headers, None)


def request(method: str, url: str, params: dict = None, data = None, json_data = None, headers: dict = None, timeout: int = 15, **kwargs) -> Response:
    """Dispatches a mock-requests HTTP call using urllib.request."""
    headers = headers or {}
    
    # Process URL query params
    if params:
        query = urllib.parse.urlencode(params)
        url = f"{url}?{query}" if "?" not in url else f"{url}&{query}"
    
    req_data = None
    if json_data is not None:
        req_data = json.dumps(json_data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif data:
        if isinstance(data, dict):
            req_data = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif isinstance(data, str):
            req_data = data.encode("utf-8")
        else:
            req_data = data

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            content = response.read()
            resp_headers = dict(response.info())
            return Response(url, status, content, resp_headers)
    except HTTPError as e:
        return Response(url, e.code, e.read(), dict(e.headers))
    except URLError as e:
        raise RuntimeError(f"Connection failed to {url}: {e.reason}")


def get(url: str, params: dict = None, **kwargs) -> Response:
    """Helper method for HTTP GET."""
    return request("GET", url, params=params, **kwargs)


def post(url: str, data = None, json = None, **kwargs) -> Response:
    """Helper method for HTTP POST."""
    return request("POST", url, data=data, json_data=json, **kwargs)
