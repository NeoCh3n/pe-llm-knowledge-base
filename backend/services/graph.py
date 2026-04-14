from __future__ import annotations

from typing import Any

from backend.config import get_settings

settings = get_settings()


class Neo4jGraphStore:
    def __init__(self) -> None:
        self._driver = None
        self._enabled = bool(settings.neo4j_uri)
        if self._enabled:
            try:
                from neo4j import GraphDatabase

                self._driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_username, settings.neo4j_password),
                )
            except Exception:
                self._driver = None

    @property
    def enabled(self) -> bool:
        return self._driver is not None

    def health(self) -> dict[str, Any]:
        return {
            "configured": self._enabled,
            "connected": self.enabled,
            "uri": settings.neo4j_uri,
        }

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
