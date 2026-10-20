import re
import unicodedata

_PREPOSITIONS = {"da", "de", "do", "das", "dos"}
_CPF_PATTERN = re.compile(r"^CPF\s+\*{3}\.\d{3}\.\d{3}-\*{2}$")


def normalize_name(name: str) -> str:
    if not name:
        return ""
    # Remove accents via NFKD decomposition
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    upper = ascii_text.upper()
    tokens = upper.split()
    filtered = [t for t in tokens if t.lower() not in _PREPOSITIONS]
    return " ".join(filtered)


def is_masked_cpf(text: str) -> bool:
    return bool(_CPF_PATTERN.match(text.strip()))
