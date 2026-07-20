"""
Unit tests for Reciprocal Rank Fusion (Step 18). Pure math, no I/O.
"""

from app.services.search.fusion import reciprocal_rank_fusion


def test_single_list_preserves_rank_order():
    result = reciprocal_rank_fusion([["a", "b", "c"]])

    ids_in_order = [item_id for item_id, score in result]
    assert ids_in_order == ["a", "b", "c"]


def test_item_ranked_first_in_both_lists_wins():
    dense = ["a", "b", "c"]
    sparse = ["a", "c", "b"]

    result = reciprocal_rank_fusion([dense, sparse])

    assert result[0][0] == "a"  # top in both lists -> highest fused score


def test_item_confirmed_by_both_lists_beats_item_in_only_one():
    # "b" ranks #2 in both lists (confirmed twice); "a" ranks #1 in only
    # one list and is absent from the other - this directly verifies the
    # Step 18 claim that RRF rewards agreement across multiple retrieval
    # paths, not just a single high rank.
    dense = ["x", "b", "z"]
    sparse = ["y", "b", "w"]

    result = reciprocal_rank_fusion([dense, sparse])

    fused_scores = dict(result)
    assert fused_scores["b"] > fused_scores["x"]
    assert fused_scores["b"] > fused_scores["y"]


def test_empty_lists_produce_empty_result():
    result = reciprocal_rank_fusion([[], []])
    assert result == []


def test_k_parameter_affects_score_magnitude_not_order():
    ranked_list = [["a", "b", "c"]]

    result_default_k = reciprocal_rank_fusion(ranked_list, k=60)
    result_small_k = reciprocal_rank_fusion(ranked_list, k=1)

    # Different k changes the actual score values...
    assert result_default_k[0][1] != result_small_k[0][1]
    # ...but should NOT change the relative order for a single list
    assert [i for i, s in result_default_k] == [i for i, s in result_small_k]