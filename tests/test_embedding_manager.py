import os
import numpy as np
import pytest
from ai_agent.memory.embedding.embedding_manager import load_embedding

def test_load_embedding(temp_dir):
    embedding_file = os.path.join(temp_dir, "test.npy")
    test_embedding = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    np.save(embedding_file, test_embedding)

    loaded = load_embedding(embedding_file)
    np.testing.assert_array_equal(loaded, test_embedding)

def test_load_nonexistent_embedding():
    result = load_embedding("nonexistent_file_12345.npy")
    assert result is None
