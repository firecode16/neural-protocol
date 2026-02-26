import asyncio
from typing import Dict, List
from ..agent.base_ws import WSNeuralAgent
from ..core.signal import NeuralSignal, NeuralSignalType

class WSSalesAgent(WSNeuralAgent):
    def __init__(self, **kwargs) -> None:
        super().__init__("ventas", **kwargs)
        self.pipeline: List[Dict] = []
        self.closed_deals: List[Dict] = []

    async def handle_signal(self, signal: NeuralSignal) -> None:
        if signal.signal_type == NeuralSignalType.NOREPINEPHRINE:
            await self._handle_opportunity(signal)
        elif signal.signal_type == NeuralSignalType.DOPAMINE:
            await self._handle_deal_confirmed(signal)
        else:
            await super().handle_signal(signal)

    async def _handle_opportunity(self, signal: NeuralSignal) -> None:
        opp = signal.payload
        deal_id = f"DEAL-{len(self.pipeline)+1:03d}"
        base_price = opp.get("estimated_value", 99.99)
        discount = 0.20 if base_price > 150 else 0.10
        final_price = round(base_price * (1 - discount), 2)

        deal = {
            "deal_id": deal_id,
            "ticket_id": opp.get("ticket_id"),
            "customer": opp.get("customer"),
            "base_price": base_price,
            "discount": discount,
            "final_price": final_price,
            "status": "proposed",
        }
        self.pipeline.append(deal)
        self._info(f"💼 {deal_id}: ${base_price:.2f} → ${final_price:.2f} ({discount:.0%} desc)")

        await asyncio.sleep(0.15)
        deal["status"] = "accepted"
        self._info(f"✅ Cliente aceptó {deal_id}")

        await self.transmit(
            "facturacion",
            NeuralSignalType.GLUTAMATE,
            {
                "deal_id": deal_id,
                "ticket_id": deal["ticket_id"],
                "customer": deal["customer"],
                "amount": final_price,
                "product": "storage_expansion",
                "discount_applied": discount,
            },
        )

    async def _handle_deal_confirmed(self, signal: NeuralSignal) -> None:
        deal_id = signal.payload.get("deal_id")
        for deal in self.pipeline:
            if deal["deal_id"] == deal_id:
                deal["status"] = "closed"
                self.closed_deals.append(deal)
                self._info(f"💰 {deal_id} cerrado y cobrado!")