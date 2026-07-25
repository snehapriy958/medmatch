from app.embeddings import EmbeddingModel


def test_embedding_generation():

    model = EmbeddingModel()

    vector = model.encode(
        "Patient has Stage III breast cancer."
    )

    assert isinstance(vector, list)

    assert len(vector) > 0

    assert all(
        isinstance(value, float)
        for value in vector
    )