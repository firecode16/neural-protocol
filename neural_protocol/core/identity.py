import hashlib
import time
import uuid
from dataclasses import dataclass, field

@dataclass
class NeuralIdentity:
    agent_id: str
    neural_hash: str
    created_at: float = field(default_factory=time.time)

    @classmethod
    def generate(cls, agent_id: str) -> "NeuralIdentity":
        raw = f"{agent_id}:{time.time()}:{uuid.uuid4()}"
        neural_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return cls(agent_id=agent_id, neural_hash=neural_hash)

    def __str__(self) -> str:
        return f"[{self.agent_id}#{self.neural_hash[:6]}]"