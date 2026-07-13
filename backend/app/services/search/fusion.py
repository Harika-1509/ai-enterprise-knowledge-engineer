from collections import defaultdict


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k: int = 60
) -> list[tuple[str, float]]:
    """
    Merges multiple ranked lists of point IDs into a single fused ranking
    using Reciprocal Rank Fusion. Works purely on rank position, which
    sidesteps the problem of dense (cosine, 0-1) and sparse (BM25,
    unbounded) scores being on incompatible scales.

    Returns a list of (point_id, fused_score) sorted best-first.
    """
    scores: dict[str, float] = defaultdict(float)

    for ranked_list in ranked_lists:
        for rank, point_id in enumerate(ranked_list, start=1):
            scores[point_id] += 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)