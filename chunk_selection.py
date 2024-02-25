from vectorize import vectorize
from scoring import base_prompt
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def get_project_context(text_chunks, embeddings, top_k=10):
    _, base_prompt_emb = vectorize([base_prompt], chunk_size=99999)

    similarities = cosine_similarity(base_prompt_emb, embeddings)[0]
    sorted_indices = np.argsort(similarities)[::-1]

    top_indices = sorted_indices[:top_k]
    top_chunks = [text_chunks[i] for i in top_indices]

    return '\n-----\n'.join(top_chunks)
