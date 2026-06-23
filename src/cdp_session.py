import json
import time
from typing import Any

from websocket import WebSocket, WebSocketTimeoutException, create_connection


class CdpSession:
    """
    Chrome DevTools Protocol session over a WebSocket connection.

    Sends CDP commands to a Chromium target and waits for the matching response,
    ignoring unrelated events on the same socket.
    """

    def __init__(self, ws_url: str) -> None:
        """
        Opens a WebSocket connection to a Chromium DevTools target.

        Args:
            ws_url (str): WebSocket debugger URL for the target page.
        """
        self._ws: WebSocket = create_connection(ws_url, timeout=300)
        self._next_id: int = 0

    def close(self) -> None:
        """Closes the underlying WebSocket connection."""
        self._ws.close()

    def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = 300,
    ) -> dict[str, Any]:
        """
        Sends a CDP command and blocks until the matching response arrives.

        Args:
            method (str): CDP method name, for example ``Page.navigate``.
            params (dict[str, Any] | None): Optional method parameters.
            timeout (float): Maximum seconds to wait for a response.

        Returns:
            dict[str, Any]: The ``result`` object from the CDP response.

        Raises:
            RuntimeError: If Chromium returns a CDP error for the command.
            TimeoutError: If no matching response arrives before ``timeout``.
        """
        self._next_id += 1
        message_id: int = self._next_id
        self._ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))

        deadline: float = time.time() + timeout
        while time.time() < deadline:
            self._ws.settimeout(max(0.1, deadline - time.time()))
            try:
                raw_message: str | bytes = self._ws.recv()
            except WebSocketTimeoutException:
                continue

            raw: str = raw_message.decode("utf-8") if isinstance(raw_message, bytes) else raw_message
            response: dict[str, Any] = json.loads(raw)
            if response.get("id") != message_id:
                continue
            if "error" in response:
                raise RuntimeError(response["error"])
            return response.get("result", {})

        raise TimeoutError(f"Timed out waiting for CDP response to {method}")
