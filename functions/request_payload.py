from typing import Any

from dataclasses import dataclass


@dataclass
class RequestPayload:
    body: dict
    queryParams: dict
    headers: dict
    user: dict | None = None

    def __getattr__(self, name: str) -> Any:
        if name in self.queryParams:
            return self.queryParams[name]

        if name in self.body:
            return self.body[name]

        # If not found in either, raise AttributeError
        raise AttributeError(
            f"'{self.__class__.__name__}' has no attribute '{name}' "
            f"(not found in queryParams or body)"
        )


@dataclass
class DynamodbStreamPayload:
    body: dict
