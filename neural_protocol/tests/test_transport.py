import asyncio
import unittest
from neural_protocol.transport.local import LocalTransport
from neural_protocol.core.signal import NeuralSignal, NeuralSignalType

class TestLocalTransport(unittest.IsolatedAsyncioTestCase):
    async def test_register_and_send(self):
        transport = LocalTransport()
        await transport.register_agent("agent1", "hash1")
        await transport.register_agent("agent2", "hash2")

        signal = NeuralSignal(
            signal_type=NeuralSignalType.DOPAMINE,
            source="hash1",
            target="hash2",
            payload={"msg": "hello"}
        )
        success = await transport.send(signal)
        self.assertTrue(success)

        # agent2 should receive
        received = await transport.receive("hash2")
        self.assertEqual(received.source, "hash1")
        self.assertEqual(received.target, "hash2")
        self.assertEqual(received.payload["msg"], "hello")

    async def test_resolve(self):
        transport = LocalTransport()
        await transport.register_agent("support", "hash_support")
        h = await transport.resolve("support")
        self.assertEqual(h, "hash_support")


if __name__ == "__main__":
    unittest.main()