"""NeuralProtocol - Base library for agent communication."""
from .core.signal import NeuralSignal, NeuralSignalType
from .core.identity import NeuralIdentity
from .core.synapse import Synapse
from .agent.base import NeuralAgent
from .agent.base_ws import WSNeuralAgent
from .transport.local import LocalTransport
from .transport.websocket import connect_websocket, WebSocketConnection

__all__ = [
    "NeuralSignal",
    "NeuralSignalType",
    "NeuralIdentity",
    "Synapse",
    "NeuralAgent",
    "WSNeuralAgent",
    "LocalTransport",
    "connect_websocket",
    "WebSocketConnection",
]