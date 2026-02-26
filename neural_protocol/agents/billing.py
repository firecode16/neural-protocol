import asyncio
import time
from typing import Dict, List
from ..agent.base import NeuralAgent
from ..core.signal import NeuralSignal, NeuralSignalType

class BillingAgent(NeuralAgent):
    def __init__(self, transport):
        super().__init__("facturacion", transport)
        self.transactions: List[Dict] = []
        self.total_revenue: float = 0.0

    async def handle_signal(self, signal: NeuralSignal) -> None:
        if signal.signal_type == NeuralSignalType.GLUTAMATE:
            await self._process_payment(signal)
        else:
            await super().handle_signal(signal)

    async def _process_payment(self, signal: NeuralSignal) -> None:
        data = signal.payload
        tx_id = f"TX-{len(self.transactions)+1:04d}"
        amount = data.get("amount", 0.0)

        self._info(f"💳 Procesando pago {tx_id}: ${amount:.2f}...")
        await asyncio.sleep(0.1)

        tx = {
            "tx_id": tx_id,
            "deal_id": data.get("deal_id"),
            "ticket_id": data.get("ticket_id"),
            "customer": data.get("customer"),
            "amount": amount,
            "product": data.get("product"),
            "status": "paid",
            "timestamp": time.time(),
        }
        self.transactions.append(tx)
        self.total_revenue += amount

        self._info(f"✅ Pago {tx_id} APROBADO ${amount:.2f} | Revenue total: ${self.total_revenue:.2f}")

        await self.broadcast(
            signal_type=NeuralSignalType.DOPAMINE,
            payload={
                "tx_id": tx_id,
                "deal_id": data.get("deal_id"),
                "ticket_id": data.get("ticket_id"),
                "amount": amount,
                "transaction_complete": True,
                "message": "💰 Transacción completada con éxito",
            },
        )