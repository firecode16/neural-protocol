import asyncio
import time
from typing import Dict
from ..agent.base_ws import WSNeuralAgent
from ..core.signal import NeuralSignal, NeuralSignalType

class WSSupportAgent(WSNeuralAgent):
    UPSELL_KEYWORDS = ["lento", "slow", "storage", "espacio", "lleno", "capacidad"]

    def __init__(self, **kwargs) -> None:
        super().__init__("soporte", **kwargs)
        self.open_tickets: Dict[str, Dict] = {}

    async def handle_signal(self, signal: NeuralSignal) -> None:
        if signal.signal_type == NeuralSignalType.ACTION_POTENTIAL:
            await self._handle_customer_request(signal)
        elif signal.signal_type == NeuralSignalType.DOPAMINE:
            await self._handle_success(signal)
        else:
            await super().handle_signal(signal)

    async def _handle_customer_request(self, signal: NeuralSignal) -> None:
        issue = signal.payload.get("issue", "")
        ticket_id = f"TKT-{len(self.open_tickets)+1:03d}"
        self.open_tickets[ticket_id] = {
            "customer": signal.source,
            "issue": issue,
            "status": "open",
            "created_at": time.time(),
        }
        self._info(f"🎫 {ticket_id}: '{issue}'")

        if any(kw in issue.lower() for kw in self.UPSELL_KEYWORDS):
            self._info(f"💡 Oportunidad detectada en {ticket_id}")
            await asyncio.sleep(0.1)
            await self.transmit(
                "ventas",
                NeuralSignalType.NOREPINEPHRINE,
                {
                    "ticket_id": ticket_id,
                    "customer": signal.source,
                    "issue": issue,
                    "opportunity": "storage_expansion",
                    "estimated_value": 199.99,
                    "urgency": "high",
                },
            )
        else:
            self.open_tickets[ticket_id]["status"] = "resolved"
            self._info(f"✅ {ticket_id} resuelto")

    async def _handle_success(self, signal: NeuralSignal) -> None:
        ticket_id = signal.payload.get("ticket_id", "?")
        amount = signal.payload.get("amount", 0)
        if ticket_id in self.open_tickets:
            self.open_tickets[ticket_id]["status"] = "converted"
            self._info(f"🎉 {ticket_id} CONVERTIDO ${amount:.2f}")