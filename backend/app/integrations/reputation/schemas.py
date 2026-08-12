from dataclasses import dataclass, field


@dataclass
class ReputationResult:
    verdict: str  # "clean" | "suspicious" | "malicious"
    categories: list[str] = field(default_factory=list)
    provider: str = "unknown"
