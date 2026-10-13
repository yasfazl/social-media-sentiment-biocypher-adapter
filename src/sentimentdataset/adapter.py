"""BioCypher adapter for the social-media sentiment CSV dataset."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any


class SentimentAdapter:
    """Convert sentiment records into a User, Post, Emotion, and Hashtag graph."""

    REQUIRED_COLUMNS = {
        "Text",
        "Sentiment",
        "Timestamp",
        "User",
        "Platform",
        "Hashtags",
        "Retweets",
        "Likes",
        "Country",
    }

    def __init__(self, data_source: str | Path, **kwargs: Any) -> None:
        self.data_source = data_source
        self.config = kwargs

    def get_nodes(self) -> Iterator[tuple[str, str, dict[str, Any]]]:
        """Yield unique posts and their referenced users, emotions, and hashtags."""
        seen_entities: set[tuple[str, str]] = set()
        for post_id, row, provenance in self._unique_posts():
            yield post_id, "social_media_post", self._post_properties(row, provenance)

            for label, value, property_name in (
                ("user", self._value(row, "User"), "display_name"),
                ("emotion", self._value(row, "Sentiment"), "name"),
            ):
                if value is None:
                    continue
                entity_id = self._entity_id(label, value)
                if (label, entity_id) not in seen_entities:
                    seen_entities.add((label, entity_id))
                    yield entity_id, label, {property_name: value}

            for hashtag in self._hashtags(row):
                hashtag_id = self._entity_id("hashtag", hashtag)
                if ("hashtag", hashtag_id) not in seen_entities:
                    seen_entities.add(("hashtag", hashtag_id))
                    yield hashtag_id, "hashtag", {"name": hashtag}

    def get_edges(self) -> Iterator[tuple[str, str, str, dict[str, Any]]]:
        """Yield unique POSTED, EXPRESSES, and HAS_TAG relationships."""
        for post_id, row, _ in self._unique_posts():
            user = self._value(row, "User")
            if user is not None:
                yield self._entity_id("user", user), post_id, "posted", {}

            emotion = self._value(row, "Sentiment")
            if emotion is not None:
                yield post_id, self._entity_id("emotion", emotion), "expresses", {}

            for hashtag in self._hashtags(row):
                yield post_id, self._entity_id("hashtag", hashtag), "has_tag", {}

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "SentimentAdapter",
            "data_source": str(self.data_source),
            "data_type": "csv",
            "version": "0.1.0",
            "adapter_class": "SentimentAdapter",
        }

    def validate_data_source(self) -> bool:
        try:
            with Path(self.data_source).open(encoding="utf-8", newline="") as handle:
                return self.REQUIRED_COLUMNS.issubset(set(csv.DictReader(handle).fieldnames or []))
        except (OSError, csv.Error):
            return False

    def _unique_posts(
        self,
    ) -> Iterator[tuple[str, dict[str | None, str | None], dict[str, list[str]]]]:
        posts: dict[str, dict[str | None, str | None]] = {}
        provenance: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: {"source_row_ids": [], "source_legacy_indices": []}
        )
        for row in self._rows():
            post_id = self._post_id(row)
            posts.setdefault(post_id, row)
            for field_name, property_name in (
                ("", "source_row_ids"),
                ("Unnamed: 0", "source_legacy_indices"),
            ):
                value = self._value(row, field_name)
                if value is not None and value not in provenance[post_id][property_name]:
                    provenance[post_id][property_name].append(value)
        for post_id, row in posts.items():
            yield post_id, row, provenance[post_id]

    def _rows(self) -> Iterator[dict[str | None, str | None]]:
        with Path(self.data_source).open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not self.REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
                raise ValueError("CSV is missing one or more required sentiment columns")
            yield from reader

    def _post_id(self, row: dict[str | None, str | None]) -> str:
        payload = {
            "user": self._identity_value(self._value(row, "User")),
            "timestamp": self._timestamp(self._value(row, "Timestamp")) or "",
            "text": self._identity_value(self._value(row, "Text")),
            "emotion": self._identity_value(self._value(row, "Sentiment")),
            "platform": self._identity_value(self._value(row, "Platform")),
            "country": self._identity_value(self._value(row, "Country")),
            "likes": self._number(self._value(row, "Likes")),
            "retweets": self._number(self._value(row, "Retweets")),
            "hashtags": sorted(self._hashtags(row)),
        }
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return f"post:{hashlib.sha256(canonical_payload.encode()).hexdigest()[:16]}"

    def _post_properties(
        self, row: dict[str | None, str | None], provenance: dict[str, list[str]]
    ) -> dict[str, Any]:
        properties: dict[str, Any] = {
            "source_row_ids": provenance["source_row_ids"],
            "source_legacy_indices": provenance["source_legacy_indices"],
        }
        for field_name, property_name in (
            ("Text", "text"),
            ("Timestamp", "timestamp"),
            ("Platform", "platform"),
            ("Country", "country"),
        ):
            value = self._value(row, field_name)
            if value is not None:
                properties[property_name] = self._timestamp(value) if field_name == "Timestamp" else value
        for field_name, property_name in (("Retweets", "retweets"), ("Likes", "likes")):
            value = self._number(self._value(row, field_name))
            if value is not None:
                properties[property_name] = value
        return properties

    @staticmethod
    def _value(row: dict[str | None, str | None], field_name: str | None) -> str | None:
        value = row.get(field_name)
        return value.strip() if value is not None and value.strip() else None

    @staticmethod
    def _timestamp(value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").isoformat(sep=" ")
        except ValueError as error:
            raise ValueError(f"Invalid Timestamp value: {value}") from error

    @staticmethod
    def _number(value: str | None) -> int | float | None:
        try:
            number = float(value) if value is not None else None
        except ValueError:
            return None
        return int(number) if number is not None and number.is_integer() else number

    @staticmethod
    def _entity_id(label: str, value: str) -> str:
        normalized = value.strip().casefold()
        return f"{label}:{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"

    @staticmethod
    def _identity_value(value: str | None) -> str:
        return value.casefold() if value is not None else ""

    def _hashtags(self, row: dict[str | None, str | None]) -> Iterator[str]:
        value = self._value(row, "Hashtags")
        if value is None:
            return
        seen: set[str] = set()
        for match in re.finditer(r"(?<!\w)#([^\s#]+)", value):
            hashtag = match.group(1).strip().casefold()
            if hashtag and hashtag not in seen:
                seen.add(hashtag)
                yield hashtag
