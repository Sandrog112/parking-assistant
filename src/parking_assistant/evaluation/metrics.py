import time
from functools import wraps


def measure_latency(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return {"result": result, "latency_seconds": round(elapsed, 4)}
    return wrapper


def recall_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    retrieved_at_k = set(retrieved[:k])
    return len(relevant & retrieved_at_k) / len(relevant)


def precision_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    retrieved_at_k = retrieved[:k]
    if not retrieved_at_k:
        return 0.0
    hits = sum(1 for doc in retrieved_at_k if doc in relevant)
    return hits / len(retrieved_at_k)


def retrieval_quality(queries: list[dict], retrieve_fn, k: int = 3) -> dict:
    total_recall = 0.0
    total_precision = 0.0
    total_latency = 0.0
    n = len(queries)

    for q in queries:
        query_text = q["query"]
        expected = set(q["relevant"])

        start = time.perf_counter()
        retrieved = retrieve_fn(query_text, limit=k)
        latency = time.perf_counter() - start

        total_recall += recall_at_k(expected, retrieved, k)
        total_precision += precision_at_k(expected, retrieved, k)
        total_latency += latency

    return {
        "avg_recall_at_k": round(total_recall / n, 4) if n else 0.0,
        "avg_precision_at_k": round(total_precision / n, 4) if n else 0.0,
        "avg_latency_seconds": round(total_latency / n, 4) if n else 0.0,
        "num_queries": n,
    }
