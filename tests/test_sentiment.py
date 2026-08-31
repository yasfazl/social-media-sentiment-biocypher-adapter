"""Tests for the v3 social-media sentiment graph adapter."""

import csv
from pathlib import Path

import pytest

from sentimentdataset.csv.adapters.sentiment import SentimentAdapter

HEADERS = [
    "",
    "Unnamed: 0",
    "Text",
    "Sentiment",
    "Timestamp",
    "User",
    "Platform",
    "Hashtags",
    "Retweets",
    "Likes",
    "Country",
    "Year",
    "Month",
    "Day",
    "Hour",
]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def sample_row(**overrides: str) -> dict[str, str]:
    row = {
        "": "1",
        "Unnamed: 0": "10",
        "Text": "A clear day",
        "Sentiment": " Joy ",
        "Timestamp": "2023-01-15 12:30:00",
        "User": " User123 ",
        "Platform": " Twitter ",
        "Hashtags": "#Nature #Park #Nature",
        "Retweets": "15.0",
        "Likes": "30.0",
        "Country": " USA ",
        "Year": "2023",
        "Month": "1",
        "Day": "15",
        "Hour": "12",
    }
    row.update(overrides)
    return row


class TestSentimentAdapter:
    def test_emits_exact_node_types_and_post_properties(self, tmp_path: Path) -> None:
        path = tmp_path / "sentiment.csv"
        write_csv(path, [sample_row()])

        nodes = list(SentimentAdapter(path).get_nodes())
        post = next(node for node in nodes if node[1] == "social_media_post")

        assert {node[1] for node in nodes} == {
            "user",
            "social_media_post",
            "emotion",
            "hashtag",
        }
        assert all(len(node) == 3 and isinstance(node[2], dict) for node in nodes)
        assert post[2] == {
            "text": "A clear day",
            "timestamp": "2023-01-15 12:30:00",
            "platform": "Twitter",
            "country": "USA",
            "retweets": 15,
            "likes": 30,
            "source_row_ids": ["1"],
            "source_legacy_indices": ["10"],
        }
        assert all(node[1] not in {"country", "platform"} for node in nodes)

    def test_emits_exact_relationship_types_and_directions(self, tmp_path: Path) -> None:
        path = tmp_path / "sentiment.csv"
        write_csv(path, [sample_row()])
        adapter = SentimentAdapter(path)
        nodes = {node[0]: node[1] for node in adapter.get_nodes()}
        edges = list(adapter.get_edges())

        assert {edge[2] for edge in edges} == {"posted", "expresses", "has_tag"}
        assert all(edge[0] in nodes and edge[1] in nodes for edge in edges)
        assert all(nodes[edge[0]] == "user" and nodes[edge[1]] == "social_media_post" for edge in edges if edge[2] == "posted")
        assert all(nodes[edge[0]] == "social_media_post" and nodes[edge[1]] == "emotion" for edge in edges if edge[2] == "expresses")
        assert all(nodes[edge[0]] == "social_media_post" and nodes[edge[1]] == "hashtag" for edge in edges if edge[2] == "has_tag")

    def test_ids_are_stable_and_semantic_differences_keep_posts_separate(self, tmp_path: Path) -> None:
        path = tmp_path / "sentiment.csv"
        rows = [
            sample_row(),
            sample_row(**{"": "2", "Unnamed: 0": "11", "User": "OtherUser"}),
            sample_row(**{"": "3", "Unnamed: 0": "12", "Timestamp": "2023-01-15 12:31:00"}),
            sample_row(**{"": "4", "Unnamed: 0": "13", "Platform": "Instagram"}),
            sample_row(**{"": "5", "Unnamed: 0": "14", "Country": "Canada"}),
        ]
        write_csv(path, rows)

        first_nodes = list(SentimentAdapter(path).get_nodes())
        second_nodes = list(SentimentAdapter(path).get_nodes())
        post_ids = [node[0] for node in first_nodes if node[1] == "social_media_post"]

        assert first_nodes == second_nodes
        assert len(post_ids) == 5
        assert len(set(post_ids)) == 5
        assert all(node_id.startswith("post:") for node_id in post_ids)

    def test_duplicate_records_collapse_and_preserve_all_provenance(self, tmp_path: Path) -> None:
        path = tmp_path / "sentiment.csv"
        write_csv(path, [sample_row(), sample_row(**{"": "2", "Unnamed: 0": "11"})])

        adapter = SentimentAdapter(path)
        posts = [node for node in adapter.get_nodes() if node[1] == "social_media_post"]

        assert len(posts) == 1
        assert posts[0][2]["source_row_ids"] == ["1", "2"]
        assert posts[0][2]["source_legacy_indices"] == ["10", "11"]
        assert len(list(adapter.get_edges())) == 4

    def test_hashtag_order_does_not_change_post_identity(self, tmp_path: Path) -> None:
        path = tmp_path / "sentiment.csv"
        write_csv(
            path,
            [
                sample_row(),
                sample_row(
                    **{
                        "": "2",
                        "Unnamed: 0": "11",
                        "Hashtags": "#Park #Nature #Nature",
                    }
                ),
            ],
        )

        posts = [node for node in SentimentAdapter(path).get_nodes() if node[1] == "social_media_post"]

        assert len(posts) == 1
        assert posts[0][2]["source_row_ids"] == ["1", "2"]

    def test_hashtag_and_emotion_normalization(self, tmp_path: Path) -> None:
        path = tmp_path / "sentiment.csv"
        rows = [
            sample_row(),
            sample_row(**{"": "2", "Text": "Second", "Sentiment": " happy ", "Hashtags": ""}),
            sample_row(**{"": "3", "Text": "Third", "Sentiment": "Happiness", "Hashtags": "#NATURE #New"}),
        ]
        write_csv(path, rows)

        nodes = list(SentimentAdapter(path).get_nodes())
        emotions = [node for node in nodes if node[1] == "emotion"]
        hashtags = [node for node in nodes if node[1] == "hashtag"]
        tag_edges = [edge for edge in SentimentAdapter(path).get_edges() if edge[2] == "has_tag"]

        assert {node[2]["name"] for node in emotions} == {"Joy", "happy", "Happiness"}
        assert len(emotions) == 3
        assert {node[2]["name"] for node in hashtags} == {"nature", "park", "new"}
        assert len(tag_edges) == 4

    def test_missing_hashtags_are_skipped_and_numeric_properties_preserved(self, tmp_path: Path) -> None:
        path = tmp_path / "sentiment.csv"
        write_csv(path, [sample_row(**{"Hashtags": "   ", "Likes": "12.5", "Retweets": "7"})])

        nodes = list(SentimentAdapter(path).get_nodes())
        post = next(node for node in nodes if node[1] == "social_media_post")

        assert not [node for node in nodes if node[1] == "hashtag"]
        assert not [edge for edge in SentimentAdapter(path).get_edges() if edge[2] == "has_tag"]
        assert post[2]["likes"] == 12.5
        assert post[2]["retweets"] == 7

    def test_invalid_source_columns_are_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "invalid.csv"
        path.write_text("id,name\n1,invalid\n", encoding="utf-8")

        assert SentimentAdapter(path).validate_data_source() is False

    @pytest.mark.skipif(
        not Path("data/sentimentdataset.csv").exists(),
        reason="Full sentiment dataset is not available; data/ is intentionally gitignored.",
    )
    def test_real_dataset_posted_and_expresses_counts_and_endpoints(self) -> None:
        adapter = SentimentAdapter("data/sentimentdataset.csv")
        nodes = {node_id for node_id, _, _ in adapter.get_nodes()}
        edges = list(adapter.get_edges())

        assert sum(edge[2] == "posted" for edge in edges) == 710
        assert sum(edge[2] == "expresses" for edge in edges) == 710
        assert all(source in nodes and target in nodes for source, target, _, _ in edges)
