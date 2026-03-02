import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional
from ..utils.constants import GLOBAL_ID_SEPARATOR

@dataclass
class NeuralIdentity:
    agent_id: str
    neural_hash: str
    domain: Optional[str] = None           # Nuevo: dominio del hub al que pertenece
    created_at: float = field(default_factory=time.time)

    @classmethod
    def generate(cls, agent_id: str, domain: Optional[str] = None) -> "NeuralIdentity":
        raw = f"{agent_id}:{time.time()}:{uuid.uuid4()}"
        neural_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return cls(agent_id=agent_id, neural_hash=neural_hash, domain=domain)

    @property
    def global_id(self) -> str:
        """Identificador único global: nombre@dominio (o solo nombre si no hay dominio)."""
        if self.domain:
            return f"{self.agent_id}{GLOBAL_ID_SEPARATOR}{self.domain}"
        return self.agent_id

    def __str__(self) -> str:
        # Muestra el identificador global si existe, si no el local
        display = self.global_id if self.domain else f"{self.agent_id}#{self.neural_hash[:6]}"
        return f"[{display}]"