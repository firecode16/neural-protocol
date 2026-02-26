import asyncio
import unittest
from neural_protocol.transport.local import LocalTransport
from neural_protocol.agents.support import SupportAgent
from neural_protocol.agents.sales import SalesAgent
from neural_protocol.agents.billing import BillingAgent
from neural_protocol.core.signal import NeuralSignal, NeuralSignalType
from neural_protocol.core.identity import NeuralIdentity

class TestAgents(unittest.IsolatedAsyncioTestCase):
    async def test_full_flow(self):
        transport = LocalTransport()
        support = SupportAgent(transport)
        sales = SalesAgent(transport)
        billing = BillingAgent(transport)

        await support.connect("ventas")
        await sales.connect("facturacion")

        tasks = [
            asyncio.create_task(support.run()),
            asyncio.create_task(sales.run()),
            asyncio.create_task(billing.run()),
        ]

        await asyncio.sleep(0.1)

        customer = NeuralIdentity.generate("customer")
        signal = NeuralSignal(
            signal_type=NeuralSignalType.ACTION_POTENTIAL,
            source=customer.neural_hash,
            target=support.identity.neural_hash,
            payload={"issue": "App lenta, sin storage"}
        )
        await transport.send(signal)

        await asyncio.sleep(1.0)

        self.assertGreater(len(billing.transactions), 0)
        self.assertGreater(billing.total_revenue, 0)

        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    unittest.main()