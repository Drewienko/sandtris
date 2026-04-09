"""
Tests for the high-score list-merge logic that lives in _save_high_score().

We extract the pure data transformation so we don't need pygame or a display.
"""

from __future__ import annotations


def _merge(existing: list, new_entry: dict, cap: int = 5) -> tuple[list, str]:
    scores = list(existing)
    scores.append(new_entry)
    scores.sort(key=lambda e: e.get("score", 0), reverse=True)
    scores = scores[:cap]
    best_is_new = scores[0]["score"] == new_entry["score"]
    status = "New high score!" if best_is_new else "Score saved"
    return scores, status


def _entry(score: int, player: str = "X") -> dict:
    return {"player": player, "score": score}


def test_new_entry_is_inserted_sorted() -> None:
    existing = [_entry(500), _entry(300), _entry(100)]
    result, _ = _merge(existing, _entry(400))
    scores = [e["score"] for e in result]
    assert scores == sorted(scores, reverse=True)


def test_list_is_capped_at_five() -> None:
    existing = [_entry(s) for s in [900, 800, 700, 600, 500]]
    result, _ = _merge(existing, _entry(1000))
    assert len(result) == 5


def test_low_score_outside_cap_is_dropped() -> None:
    existing = [_entry(s) for s in [900, 800, 700, 600, 500]]
    result, _ = _merge(existing, _entry(10))
    assert all(e["score"] >= 500 for e in result)
    assert len(result) == 5


def test_new_top_score_gives_new_high_score_status() -> None:
    existing = [_entry(500), _entry(300)]
    _, status = _merge(existing, _entry(1000))
    assert status == "New high score!"


def test_non_top_score_gives_score_saved_status() -> None:
    existing = [_entry(1000), _entry(800)]
    _, status = _merge(existing, _entry(200))
    assert status == "Score saved"


def test_first_ever_score_is_new_high_score() -> None:
    _, status = _merge([], _entry(42))
    assert status == "New high score!"


def test_tied_top_score_gives_new_high_score_status() -> None:
    existing = [_entry(1000, "OLD")]
    result, status = _merge(existing, _entry(1000, "NEW"))
    assert status == "New high score!"
