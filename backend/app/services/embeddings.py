
import hashlib
import math
import re
from collections import Counter

DIM = 384
_TOKEN_RE = re.compile(r"[a-zA-Z\u0900-\u097F]+|\d+", re.UNICODE)  # latin + devanagari + digits


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _hash_bucket(token: str, dim: int = DIM) -> int:
    h = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(h, 16) % dim


class HashingEmbeddingFunction:
    """Chroma EmbeddingFunction-compatible callable. TF-hashing + bigram
    hashing + L2 normalization. No downloads, fully deterministic."""

    def name(self) -> str:
        return "hashing-embedding-v1"

    def __call__(self, input: list[str]) -> list[list[float]]:
        vectors = []
        for text in input:
            tokens = _tokenize(text)
            counts = Counter()
            for tok in tokens:
                counts[_hash_bucket(tok)] += 1.0
            for a, b in zip(tokens, tokens[1:]):
                counts[_hash_bucket(a + "_" + b)] += 0.5

            vec = [0.0] * DIM
            for idx, val in counts.items():
                vec[idx] = val
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vec = [v / norm for v in vec]
            vectors.append(vec)
        return vectors
