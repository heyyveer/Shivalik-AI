
import json
import re
from functools import lru_cache
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.rag.embeddings import get_embeddings
from app.rag.vectorstore import get_collection, load_chunks

CHUNKS_FILE = Path("data/processed/chunks.json")

DEFAULT_TOP_K = 5
CANDIDATE_K = 15
RRF_K = 60


def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())



@lru_cache(maxsize=1)
def load_bm25_index():
    chunks = load_chunks()

    tokenized_corpus = [
        tokenize(chunk["content"])
        for chunk in chunks
    ]

    bm25 = BM25Okapi(tokenized_corpus)

    chunk_lookup = {
        chunk["chunk_id"]: chunk
        for chunk in chunks
    }

    return bm25, chunks, chunk_lookup



def semantic_search(query, top_k=CANDIDATE_K):
    collection = get_collection()
    embeddings = get_embeddings()

    count = collection.count()

    if count == 0:
        return []

    query_vector = embeddings.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []

    for chunk_id, content, metadata, distance in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        retrieved.append({
            "chunk_id": chunk_id,
            "content": content,
            "metadata": metadata,
            "semantic_similarity": 1 - distance,
        })

    return retrieved


def keyword_search(query, top_k=CANDIDATE_K):
    bm25, chunks, _ = load_bm25_index()

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    scores = bm25.get_scores(query_tokens)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True,
    )

    results = []

    for index in ranked_indices[:top_k]:
        if scores[index] <= 0:
            continue

        chunk = chunks[index]

        results.append({
            "chunk_id": chunk["chunk_id"],
            "content": chunk["content"],
            "metadata": chunk["metadata"],
            "bm25_score": float(scores[index]),
        })

    return results


def reciprocal_rank_fusion(result_lists, k=RRF_K):
    fused = {}

    for results in result_lists:
        for rank, result in enumerate(results, start=1):
            chunk_id = result["chunk_id"]

            if chunk_id not in fused:
                fused[chunk_id] = {
                    **result,
                    "rrf_score": 0.0,
                }

            fused[chunk_id]["rrf_score"] += 1 / (k + rank)

            # Preserve scores from both retrieval methods
            for score_key in ("semantic_similarity", "bm25_score"):
                if score_key in result:
                    fused[chunk_id][score_key] = result[score_key]

    return sorted(
        fused.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )


CATEGORY_KEYWORDS = {
    "placements": [
        "placement", "placements", "recruiter",
        "recruitment", "internship", "internships",
        "career opportunities", "campus drive",
        "salary package", "highest package"
    ],
    "fees": [
        "fee", "fees", "tuition", "hostel charges",
        "fee structure", "scholarship"
    ],
    "admissions": [
        "admission", "admissions", "eligibility",
        "application process", "how to apply"
    ],
    "research": [
        "research", "publication", "patent",
        "laboratory", "innovation"
    ],
}


def detect_query_category(query):
    query = query.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(
            re.search(
                rf"\b{re.escape(keyword)}\b",
                query
            )
            for keyword in keywords
        ):
            return category

    return None


def diversify_results(results, top_k=5, max_per_source=2):
    selected = []
    source_counts = {}

    for result in results:
        source = result["metadata"].get(
            "source",
            result["chunk_id"]
        )

        if source_counts.get(source, 0) >= max_per_source:
            continue

        selected.append(result)
        source_counts[source] = (
            source_counts.get(source, 0) + 1
        )

        if len(selected) >= top_k:
            break

    return selected


def retrieve_documents(query, top_k=DEFAULT_TOP_K):
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    candidate_k = max(CANDIDATE_K, top_k, 50)

    semantic_results = semantic_search(query, candidate_k)
    keyword_results = keyword_search(query, candidate_k)

    fused_results = reciprocal_rank_fusion(
        [semantic_results, keyword_results]
    )

    detected_category = detect_query_category(query)

    CATEGORY_BOOST = 0.015

    for result in fused_results:
        result["detected_category"] = detected_category

        result["final_score"] = result["rrf_score"]

        if (
            detected_category
            and result["metadata"].get("category")
            == detected_category
        ):
            result["final_score"] += CATEGORY_BOOST

    fused_results.sort(
        key=lambda item: item["final_score"],
        reverse=True
    )

    return diversify_results(
        fused_results,
        top_k=top_k,
        max_per_source=2
    )



if __name__ == "__main__":
    question = input("Ask Shivalik AI: ")

    results = retrieve_documents(question)

    for index, result in enumerate(results, start=1):
        print(f"\n========== RESULT {index} ==========")
        print("Title:", result["metadata"].get("title"))
        print("Category:", result["metadata"].get("category"))
        print("Source:", result["metadata"].get("source"))
        print("RRF Score:", round(result["rrf_score"], 6))
        print(
            "Semantic Similarity:",
            result.get("semantic_similarity", "N/A")
        )
        print("BM25 Score:", result.get("bm25_score", "N/A"))
        print("Content:", result["content"][:700])
