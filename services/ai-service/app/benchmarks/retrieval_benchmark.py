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
    with SessionLocal() as db:

        repository = MatchingRepository(db)

        # Only embedding generation is required for this benchmark.
        # Repository dependencies are intentionally omitted because
        # generate_embedding() does not use them.
        embedding_service = EmbeddingService(
            criteria_repository=None,
            patient_note_repository=None,
        )

        correct = 0

        for test in TEST_QUERIES:

            print("=" * 80)
            print("Query:")
            print(test["query"])

            embedding = embedding_service.generate_embedding(
                test["query"]
            )

            results = repository.find_similar_criteria(
                embedding=embedding,
                limit=settings.TOP_K_RESULTS,
            )

            found = False

            for index, result in enumerate(results, start=1):

                print(
                    f"{index}. "
                    f"{result['description']} "
                    f"(distance={result['distance']:.4f})"
                )

                if (
                    test["expected"].lower()
                    in result["description"].lower()
                ):
                    found = True

            if found:
                correct += 1
                print("PASS")
            else:
                print("FAIL")

        accuracy = (correct / len(TEST_QUERIES)) * 100

        print("=" * 80)
        print(
            f"Accuracy: {accuracy:.2f}% "
            f"({correct}/{len(TEST_QUERIES)})"
        )


if __name__ == "__main__":
    main()