import asyncio
from typing import Dict, List
from ..agent.base import NeuralAgent
from ..core.signal import NeuralSignal, NeuralSignalType

class SalesAgent(NeuralAgent):
    DISCOUNT_THRESHOLD = 150.0

    def __init__(self, transport):
        super().__init__("ventas", transport)
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

        self._info(
            f"📊 Oportunidad recibida: {opp.get('opportunity')} "
            f"(valor est. ${opp.get('estimated_value', 0):.2f})"
        )

        base_price = opp.get("estimated_value", 99.99)
        discount = 0.20 if base_price > self.DISCOUNT_THRESHOLD else 0.10
        final_price = round(base_price * (1 - discount), 2)

        deal = {
            "deal_id": deal_id,
            "ticket_id": opp.get("ticket_id"),
            "customer": opp.get("customer"),
            "opportunity": opp.get("opportunity"),
            "base_price": base_price,
            "discount": discount,
            "final_price": final_price,
            "status": "proposed",
        }
        self.pipeline.append(deal)

        self._info(
            f"💼 Deal {deal_id}: ${base_price:.2f} → ${final_price:.2f} "
            f"({discount:.0%} descuento)"
        )

        await asyncio.sleep(0.15)
        self._info(f"✅ Cliente aceptó {deal_id}")
        deal["status"] = "accepted"

        await self.transmit(
            target_name="facturacion",
            signal_type=NeuralSignalType.GLUTAMATE,
            payload={
                "deal_id": deal_id,
                "ticket_id": deal["ticket_id"],
                "customer": deal["customer"],
                "amount": final_price,
                "product": deal["opportunity"],
                "discount_applied": discount,
            },
        )

    async def _handle_deal_confirmed(self, signal: NeuralSignal) -> None:
        deal_id = signal.payload.get("deal_id")
        for deal in self.pipeline:
            if deal["deal_id"] == deal_id:
                deal["status"] = "closed"
                self.closed_deals.append(deal)
                self._info(f"💰 Deal {deal_id} cerrado y cobrado!")