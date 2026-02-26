from abc import ABC, abstractmethod
from typing import Optional
from ..core.signal import NeuralSignal

class Transport(ABC):
    @abstractmethod
    async def send(self, signal: NeuralSignal) -> bool:
        """Send a signal to its target (or broadcast if target empty)."""
        pass

    @abstractmethod
    async def register_agent(self, agent_id: str, agent_hash: str) -> None:
        """Register an agent so it can receive signals."""
        pass

    @abstractmethod
    async def unregister_agent(self, agent_hash: str) -> None:
        """Unregister an agent."""
        pass

    @abstractmethod
    async def resolve(self, name: str) -> Optional[str]:
        """Resolve logical agent name to neural hash."""
        pass

    @abstractmethod
    async def receive(self, agent_hash: str) -> NeuralSignal:
        """Receive the next signal for the given agent (blocking)."""
        pass