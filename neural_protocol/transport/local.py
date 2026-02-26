import asyncio
from typing import Dict, Optional
from ..core.signal import NeuralSignal
from .base import Transport

class LocalTransport(Transport):
    def __init__(self) -> None:
        self._queues: Dict[str, asyncio.Queue] = {}
        self._names: Dict[str, str] = {}   # name -> hash
        self._hashes: Dict[str, str] = {}  # hash -> name
        self._stats = {"transmitted": 0, "bytes": 0}

    async def register_agent(self, agent_id: str, agent_hash: str) -> None:
        self._queues[agent_hash] = asyncio.Queue(maxsize=1000)
        self._names[agent_id] = agent_hash
        self._hashes[agent_hash] = agent_id

    async def unregister_agent(self, agent_hash: str) -> None:
        self._queues.pop(agent_hash, None)
        name = self._hashes.pop(agent_hash, None)
        if name:
            self._names.pop(name, None)

    async def resolve(self, name: str) -> Optional[str]:
        return self._names.get(name)

    async def send(self, signal: NeuralSignal) -> bool:
        encoded = signal.encode()
        self._stats["bytes"] += len(encoded)
        self._stats["transmitted"] += 1

        targets = list(self._queues.keys()) if not signal.target else [signal.target]
        delivered = 0
        for t in targets:
            if t == signal.source:
                continue
            q = self._queues.get(t)
            if q:
                try:
                    q.put_nowait(encoded)
                    delivered += 1
                except asyncio.QueueFull:
                    pass
        return delivered > 0

    async def receive(self, agent_hash: str) -> NeuralSignal:
        q = self._queues.get(agent_hash)
        if q is None:
            raise RuntimeError(f"Agent {agent_hash} not registered")
        encoded = await q.get()
        signal = NeuralSignal.decode(encoded)
        q.task_done()
        return signal

    @property
    def stats(self) -> Dict:
        return dict(self._stats, agents=len(self._queues))