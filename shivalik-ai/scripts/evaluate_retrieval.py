
from app.rag.retriever import retrieve_documents


TEST_CASES = [
    {
        "question": "What is the BCA fee at Shivalik University?",
        "required_evidence": [
            {
                "source": "/admissions/fee-structure",
                "text": "Programme: BCA",
            }
        ],
    },
    {
        "question": "What is the hostel fee at Shivalik University?",
        "required_evidence": [
            {
                "source": "/admissions/fee-structure",
                "text": "₹ 1,00,000",
            },
            {
                "source": "/admissions/fee-structure",
                "text": "₹ 1,25,000",
            },
        ],
    },
    {
        "question": "What is the eligibility criteria for B.Tech CSE?",
        "required_evidence": [
            {
                "source": "/school-of-engineering/computer-science-engineering",
                "text": None,
            }
        ],
    },
    {
        "question": "What placement opportunities does Shivalik University offer?",
        "required_evidence": [
            {
                "source": "/placements/overview",
                "text": "internships",
            },
            {
                "source": "/placements/overview",
                "text": "mock interviews",
            },
        ],
    },
]


def evidence_matches(chunk, evidence):
    source = chunk["metadata"].get("source", "")
    content = chunk["content"].lower()

    if evidence["source"] not in source:
        return False

    required_text = evidence.get("text")

    if required_text:
        return required_text.lower() in content

    return True


def evaluate():
    hit_scores = []
    mrr_scores = []
    coverage_scores = []

    print("\n========== EVIDENCE EVALUATION ==========")

    for test in TEST_CASES:
        results = retrieve_documents(test["question"], top_k=5)

        evidence_ranks = []

        for evidence in test["required_evidence"]:
            matching_ranks = [
                rank
                for rank, chunk in enumerate(results, start=1)
                if evidence_matches(chunk, evidence)
            ]

            evidence_ranks.append(
                matching_ranks[0] if matching_ranks else None
            )

        found = sum(rank is not None for rank in evidence_ranks)
        total = len(evidence_ranks)

        coverage = found / total if total else 0
        hit = int(found > 0)

        valid_ranks = [
            rank for rank in evidence_ranks
            if rank is not None
        ]

        reciprocal_rank = (
            1 / min(valid_ranks) if valid_ranks else 0
        )

        hit_scores.append(hit)
        mrr_scores.append(reciprocal_rank)
        coverage_scores.append(coverage)

        print(f"\nQuestion: {test['question']}")
        print(f"Evidence ranks: {evidence_ranks}")
        print(f"Evidence Coverage@5: {coverage:.3f}")
        print(f"Hit@5: {hit}")
        print(f"Reciprocal Rank: {reciprocal_rank:.3f}")

    total_tests = len(TEST_CASES)

    print("\n========== FINAL METRICS ==========")
    print(f"Hit Rate@5: {sum(hit_scores)/total_tests:.3f}")
    print(f"MRR@5: {sum(mrr_scores)/total_tests:.3f}")
    print(
        f"Average Evidence Coverage@5: "
        f"{sum(coverage_scores)/total_tests:.3f}"
    )


if __name__ == "__main__":
    evaluate()
