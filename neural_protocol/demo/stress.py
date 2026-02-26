#!/usr/bin/env python3
"""Stress test with multiple concurrent transactions."""
import asyncio
import sys
import time
from ..transport.local import LocalTransport
from ..agents.support import SupportAgent
from ..agents.sales import SalesAgent
from ..agents.billing import BillingAgent
from ..core.signal import NeuralSignal, NeuralSignalType
from ..core.identity import NeuralIdentity

async def run_stress(n: int):
    transport = LocalTransport()

    support = SupportAgent(transport)
    sales = SalesAgent(transport)
    billing = BillingAgent(transport)

    await support.connect("ventas")
    await sales.connect("facturacion")
    await billing.connect("soporte")
    await billing.connect("ventas")

    tasks = [
        asyncio.create_task(support.run()),
        asyncio.create_task(sales.run()),
        asyncio.create_task(billing.run()),
    ]

    await asyncio.sleep(0.1)

    t0 = time.perf_counter()

    signals = []
    for i in range(n):
        customer = NeuralIdentity.generate(f"stress_customer_{i}")
        sig = NeuralSignal(
            signal_type=NeuralSignalType.ACTION_POTENTIAL,
            source=customer.neural_hash,
            target=support.identity.neural_hash,
            payload={
                "issue": f"App lenta, necesito más storage #{i}",
                "customer_id": f"stress_{i}",
            },
        )
        signals.append(sig)

    await asyncio.gather(*[transport.send(s) for s in signals])

    wait = min(n * 0.05, 10.0)
    await asyncio.sleep(wait)
    elapsed = time.perf_counter() - t0

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    stats = transport.stats
    print("\n📊 Resultados Stress Test:")
    print(f"   Tickets enviados:    {n}")
    print(f"   Transacciones:       {len(billing.transactions)}")
    print(f"   Señales transmitidas:{stats['transmitted']}")
    print(f"   Bytes totales:       {stats['bytes']:,}")
    print(f"   Tiempo total:        {elapsed:.2f}s")
    print(f"   Revenue total:       ${billing.total_revenue:,.2f}")
    if elapsed > 0:
        print(f"   Throughput:          {stats['transmitted']/elapsed:.0f} señales/seg")

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    asyncio.run(run_stress(n))