"""Create the Amazon MQ topology from a runner with private VPC access."""

import base64
import json
import os
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen


def main() -> None:
    endpoint = urlsplit(os.environ["MQ_CONSOLE_URL"])
    if endpoint.scheme != "https" or not endpoint.hostname or endpoint.username:
        raise ValueError("MQ_CONSOLE_URL debe ser la URL HTTPS privada de Amazon MQ")

    credentials = f"{os.environ['MQ_ADMIN_USER']}:{os.environ['MQ_ADMIN_PASSWORD']}"
    auth = base64.b64encode(credentials.encode()).decode()
    base = f"https://{endpoint.netloc}/api"
    vhost = quote("/", safe="")

    def request(method: str, path: str, data: dict) -> None:
        req = Request(
            base + path,
            data=json.dumps(data).encode(),
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
            method=method,
        )
        try:
            with urlopen(req, timeout=15):
                pass
        except HTTPError as exc:
            raise RuntimeError(f"RabbitMQ rechazó {method} {path} con HTTP {exc.code}") from None

    request("PUT", f"/exchanges/{vhost}/itineraries", {"type": "topic", "durable": True})
    request(
        "PUT",
        f"/queues/{vhost}/notifications",
        {"durable": True, "arguments": {"x-queue-type": "quorum"}},
    )
    request(
        "POST",
        f"/bindings/{vhost}/e/itineraries/q/notifications",
        {"routing_key": "itinerary.created", "arguments": {}},
    )
    print("Topología de notificaciones lista")


if __name__ == "__main__":
    main()
