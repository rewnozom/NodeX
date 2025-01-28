# AI_Agent/memory/embedding/embedding_manager.py

import os
import numpy as np
import logging

logger = logging.getLogger(__name__)

def load_embedding(file_path):
    """Load embedding from a numpy file."""
    try:
        with open(file_path, 'rb') as f:
            embedding = np.load(f)
            logger.info(f"Embedding successfully loaded from {file_path}.")
            return embedding
    except Exception as e:
        logger.error(f"Unexpected error loading embedding from {file_path}: {e}")
        return None
