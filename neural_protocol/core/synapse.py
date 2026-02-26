import time
from dataclasses import dataclass, field

@dataclass
class Synapse:
    source_hash: str
    target_hash: str
    strength: float = 1.0
    transmission_count: int = 0
    success_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)

    LEARNING_RATE = 0.05
    MIN_STRENGTH = 0.1
    MAX_STRENGTH = 2.0

    def reinforce(self) -> None:
        self.strength = min(
            self.MAX_STRENGTH,
            self.strength + self.LEARNING_RATE * (1 + self.success_rate)
        )
        self.success_count += 1
        self.transmission_count += 1
        self.last_used = time.time()

    def weaken(self) -> None:
        self.strength = max(
            self.MIN_STRENGTH,
            self.strength - self.LEARNING_RATE * 2
        )
        self.transmission_count += 1
        self.last_used = time.time()

    @property
    def success_rate(self) -> float:
        if self.transmission_count == 0:
            return 0.0
        return self.success_count / self.transmission_count

    @property
    def is_strong(self) -> bool:
        return self.strength >= 1.2

    @property
    def is_weak(self) -> bool:
        return self.strength <= 0.3

    def __str__(self) -> str:
        bar = "█" * int(self.strength * 5)
        return (
            f"Synapse {self.source_hash[:6]}→{self.target_hash[:6]} "
            f"strength={self.strength:.2f} [{bar:<10}] "
            f"success_rate={self.success_rate:.0%} tx={self.transmission_count}"
        )