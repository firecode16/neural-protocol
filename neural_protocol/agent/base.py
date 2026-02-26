import asyncio
import time
from typing import Dict, List, Optional, Callable
from ..core.signal import NeuralSignal, NeuralSignalType
from ..core.identity import NeuralIdentity
from ..core.synapse import Synapse
from ..transport.base import Transport

class NeuralAgent:
    def __init__(self, agent_id: str, transport: Transport):
        self.identity = NeuralIdentity.generate(agent_id)
        self.transport = transport
        self._synapses: Dict[str, Synapse] = {}
        self._memory: List[NeuralSignal] = []
        self._running = False
        self._handlers: Dict[NeuralSignalType, Callable] = {}
        self._log: List[str] = []

        # Register with transport
        asyncio.create_task(self.transport.register_agent(agent_id, self.identity.neural_hash))

    async def connect(self, target_name: str) -> Optional[Synapse]:
        target_hash = await self.transport.resolve(target_name)
        if not target_hash:
            self._info(f"❌ No se encontró agente: {target_name}")
            return None
        if target_hash not in self._synapses:
            syn = Synapse(self.identity.neural_hash, target_hash)
            self._synapses[target_hash] = syn
            self._info(f"🔗 Sinapsis creada → {target_name}#{target_hash[:6]}")
        return self._synapses[target_hash]

    def disconnect(self, target_hash: str) -> None:
        self._synapses.pop(target_hash, None)

    async def transmit(self, target_name: str, signal_type: NeuralSignalType, payload: Dict) -> bool:
        target_hash = await self.transport.resolve(target_name)
        if not target_hash:
            self._info(f"⚠️ Destino desconocido: {target_name}")
            return False

        if target_hash not in self._synapses:
            await self.connect(target_name)

        signal = NeuralSignal(
            signal_type=signal_type,
            source=self.identity.neural_hash,
            target=target_hash,
            payload=payload,
        )
        self._info(f"📤 {signal}")
        success = await self.transport.send(signal)
        self._memory.append(signal)

        syn = self._synapses[target_hash]
        if success:
            syn.reinforce()
        else:
            syn.weaken()
        return success

    async def broadcast(self, signal_type: NeuralSignalType, payload: Dict) -> bool:
        signal = NeuralSignal(
            signal_type=signal_type,
            source=self.identity.neural_hash,
            target="",
            payload=payload,
        )
        self._info(f"📡 BROADCAST {signal}")
        return await self.transport.send(signal)

    def on_signal(self, signal_type: NeuralSignalType) -> Callable:
        def decorator(fn: Callable) -> Callable:
            self._handlers[signal_type] = fn
            return fn
        return decorator

    async def handle_signal(self, signal: NeuralSignal) -> None:
        handler = self._handlers.get(signal.signal_type)
        if handler:
            await handler(signal)
        else:
            self._info(f"📥 Señal sin handler: {signal.signal_type.name} de {signal.source[:8]}")

    async def run(self) -> None:
        self._running = True
        self._info(f"🟢 {self.identity} en línea")
        while self._running:
            try:
                signal = await self.transport.receive(self.identity.neural_hash)
                self._memory.append(signal)
                await self.handle_signal(signal)
            except Exception as e:
                self._info(f"❌ Error procesando señal: {e}")

    def stop(self) -> None:
        self._running = False
        self._info(f"🔴 {self.identity} offline")

    def synapse_report(self) -> str:
        if not self._synapses:
            return "  (sin sinapsis)"
        return "\n".join(f"  {syn}" for syn in self._synapses.values())

    def _info(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {self.identity.agent_id:12s} | {msg}"
        self._log.append(line)
        print(line)