import unittest
from neural_protocol.core.signal import NeuralSignal, NeuralSignalType
from neural_protocol.core.identity import NeuralIdentity
from neural_protocol.core.synapse import Synapse

class TestCore(unittest.TestCase):
    def test_signal_encode_decode(self):
        sig = NeuralSignal(
            signal_type=NeuralSignalType.DOPAMINE,
            source="abc",
            target="def",
            payload={"key": "value"}
        )
        data = sig.encode()
        sig2 = NeuralSignal.decode(data)
        self.assertEqual(sig.signal_type, sig2.signal_type)
        self.assertEqual(sig.source, sig2.source)
        self.assertEqual(sig.target, sig2.target)
        self.assertEqual(sig.payload, sig2.payload)

    def test_identity_generate(self):
        id1 = NeuralIdentity.generate("test")
        id2 = NeuralIdentity.generate("test")
        self.assertNotEqual(id1.neural_hash, id2.neural_hash)

    def test_synapse_plasticity(self):
        syn = Synapse("src", "tgt", strength=1.0)
        syn.reinforce()
        self.assertGreater(syn.strength, 1.0)
        old = syn.strength
        syn.weaken()
        self.assertLess(syn.strength, old)


if __name__ == "__main__":
    unittest.main()