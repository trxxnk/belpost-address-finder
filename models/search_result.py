from dataclasses import dataclass

@dataclass
class SearchResult:
    postal_code: str
    region: str
    district: str
    city: str
    street: str
    house_numbers: str
    similarity_score: float = 0.0
    house_match: bool = False
