from __future__ import annotations


def fuzzy_match(query: str, target: str) -> tuple[bool, int]:
    """Check if query matches target as a subsequence and return a relevance score.

    Score heuristics:
      - Exact match: +500
      - Prefix match: +300
      - Word delimiter match (after '-', '_', ' ', '/'): +200
      - Substring match: +150
      - Consecutive character matches (adjacency bonus): +10 * consecutive
      - Isolated match: +2
    """
    q = query.lower()
    t = target.lower()

    if not q:
        return True, 0

    if q == t:
        return True, 500

    if t.startswith(q):
        return True, 300 + (len(q) * 10)

    # Check for word boundary delimiter match
    for delimiter in ("-", "_", " ", "/"):
        if f"{delimiter}{q}" in t:
            return True, 200 + (len(q) * 10)

    if q in t:
        return True, 150 + (len(q) * 5)

    # Subsequence matching
    q_len = len(q)
    qi = 0
    score = 0
    consecutive = 0
    last_idx = -1

    for idx, c in enumerate(t):
        if qi < q_len and c == q[qi]:
            qi += 1
            if last_idx != -1 and idx == last_idx + 1:
                consecutive += 1
                score += 10 * consecutive
            else:
                consecutive = 0
                score += 2
            last_idx = idx

    matched = (qi == q_len)
    return matched, score
