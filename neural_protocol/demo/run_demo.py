#!/usr/bin/env python3
"""Run the full neural flow demo with local transport."""
import asyncio
from ..transport.local import LocalTransport
from ..agents.support import SupportAgent
from ..agents.sales import SalesAgent
from ..agents.billing import BillingAgent
from ..core.signal import NeuralSignal, NeuralSignalType
from ..core.identity import NeuralIdentity

async def run_demo():
    transport = LocalTransport()

    support = SupportAgent(transport)
    sales = SalesAgent(transport)
    billing = BillingAgent(transport)

    # Establish synapses
    await support.connect("ventas")
    await support.connect("facturacion")
    await sales.connect("facturacion")
    await sales.connect("soporte")
    await billing.connect("soporte")
    await billing.connect("ventas")

    tasks = [
        asyncio.create_task(support.run()),
        asyncio.create_task(sales.run()),
        asyncio.create_task(billing.run()),
    ]

    await asyncio.sleep(0.1)

    # Simulate customer ticket
    customer = NeuralIdentity.generate("customer_007")
    signal = NeuralSignal(
        signal_type=NeuralSignalType.ACTION_POTENTIAL,
        source=customer.neural_hash,
        target=support.identity.neural_hash,
        payload={
            "issue": "Mi aplicación va muy lenta, me quedé sin storage",
            "customer_id": "customer_007",
            "plan": "basic",
            "severity": "medium",
        },
    )
    print("\n📨 Cliente envía señal al soporte")
    await transport.send(signal)

    # Wait for flow to complete
    await asyncio.sleep(1.0)

    # Print final state
    print("\n" + "═"*70)
    print("ESTADO FINAL")
    print("═"*70)
    print(f"💰 Revenue total Facturación: ${billing.total_revenue:.2f}")
    print(f"🎫 Tickets abiertos: {len(support.open_tickets)}")
    print(f"💼 Deals en pipeline: {len(sales.pipeline)}")
    print(f"🧾 Transacciones: {len(billing.transactions)}")

    for tid, ticket in support.open_tickets.items():
        status_icon = {"open": "🟡", "resolved": "✅", "converted": "💚"}.get(ticket["status"], "❓")
        print(f"  {status_icon} {tid}: {ticket['status']} — '{ticket['issue'][:40]}'")

    # Stop agents
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(run_demo())