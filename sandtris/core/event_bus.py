from collections import defaultdict
from typing import Any, Callable


class GameEventBus:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable[..., None]) -> None:
        self._listeners[event].append(callback)

    def emit(self, event: str, **kwargs: Any) -> None:
        for cb in self._listeners[event]:
            cb(**kwargs)
