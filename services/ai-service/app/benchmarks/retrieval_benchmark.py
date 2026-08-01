import time

from app.config.settings import settings
from app.db.session import SessionLocal
from app.repositories.matching_repository import MatchingRepository
from app.services.embedding_service import EmbeddingService


TEST_QUERIES: list[dict[str, str]] = [
    {
        "query": (
            "Patient has advanced non-small cell lung cancer. "
            "ECOG performance status 1."
        ),
        "expected": "ECOG",
    },
    {
        "query": (
            "Patient previously received immune checkpoint inhibitors."
        ),
        "expected": "checkpoint",
    },
    {
        "query": (
            "Patient has severe cardiovascular disease."
        ),
        "expected": "cardiovascular",
    },
    {
        "query": (
            "Patient has uncontrolled hypertension."
        ),
        "expected": "hypertension",
    },
    {
        "query": (
            "Patient has active autoimmune disease."
        ),
        "expected": "autoimmune",
    },
]


def main() -> None:

    print("=" * 90)
    print("MedMatch Semantic Retrieval Benchmark")
    print("=" * 90)

    total_latency = 0.0
    correct = 0

    summary: list[tuple[str, str, str, float]] = []

    with SessionLocal() as db:

        repository = MatchingRepository(db)

        embedding_service = EmbeddingService(
            criteria_repository=None,
            patient_note_repository=None,
        )

        for index, test in enumerate(TEST_QUERIES, start=1):

            print()
            print("=" * 90)
            print(f"Test Case {index}")
            print("=" * 90)

            print(f"Query    : {test['query']}")
            print(f"Expected : {test['expected']}")

            try:
                embedding = embedding_service.generate_embedding(
                    test["query"]
                )

            except Exception as exc:
                print(f"Embedding generation failed: {exc}")

                summary.append(
                    (
                        test["expected"],
                        "ERROR",
                        "FAIL",
                        0.0,
                    )
                )

                continue

            start = time.perf_counter()

            try:
                results: list[dict] = repository.find_similar_criteria(
                    embedding=embedding,
                    limit=settings.TOP_K_RESULTS,
                )

            except Exception as exc:
                print(f"Vector search failed: {exc}")

                summary.append(
                    (
                        test["expected"],
                        "ERROR",
                        "FAIL",
                        0.0,
                    )
                )

                continue

            latency = (time.perf_counter() - start) * 1000
            total_latency += latency

            print(f"\nRetrieval latency: {latency:.2f} ms\n")

            if not results:
                print("No matching criteria returned.")

                summary.append(
                    (
                        test["expected"],
                        "-",
                        "FAIL",
                        latency,
                    )
                )

                continue

            expected = test["expected"].casefold().strip()

            found = False
            matched_rank = "-"

            print("Top Retrieved Criteria")
            print("-" * 90)

            for rank, result in enumerate(results, start=1):

                description = result["description"]

                distance = result["distance"]

                print(
                    f"{rank}. "
                    f"{description}\n"
                    f"   Cosine Distance: {distance:.4f}\n"
                )

                if expected in description.casefold():

                    found = True
                    matched_rank = str(rank)

            if found:

                correct += 1

                print("Result: PASS")

                summary.append(
                    (
                        test["expected"],
                        matched_rank,
                        "PASS",
                        latency,
                    )
                )

            else:

                print("Result: FAIL")

                summary.append(
                    (
                        test["expected"],
                        "-",
                        "FAIL",
                        latency,
                    )
                )

    accuracy = (correct / len(TEST_QUERIES)) * 100

    average_latency = total_latency / len(TEST_QUERIES)

    print()
    print("=" * 90)
    print("Benchmark Summary")
    print("=" * 90)

    print(
        f"{'Expected':<20}"
        f"{'Rank':<10}"
        f"{'Result':<10}"
        f"{'Latency (ms)':<15}"
    )

    print("-" * 90)

    for expected, rank, result, latency in summary:

        print(
            f"{expected:<20}"
            f"{rank:<10}"
            f"{result:<10}"
            f"{latency:<15.2f}"
        )

    print("-" * 90)

    print(f"Accuracy           : {accuracy:.2f}%")
    print(f"Successful Queries : {correct}/{len(TEST_QUERIES)}")
    print(f"Average Latency    : {average_latency:.2f} ms")

    print("=" * 90)


if __name__ == "__main__":
    main()