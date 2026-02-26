---
```
# 🧠 NeuralProtocol

**Binary communication protocol for AI agents**  
Inspired by biological neurotransmitters – compact, fast, and self‑learning.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## Why NeuralProtocol?

Modern agent‑based systems often rely on verbose REST/JSON or GraphQL.  
NeuralProtocol offers a **binary, neurotransmitter‑inspired** alternative that is:

- **Compact** – up to 2.2× smaller than equivalent REST messages.
- **Fast** – >140,000 encode/decode operations per second (pure Python).
- **Intelligent** – built‑in Hebbian learning (synaptic plasticity).
- **Transport‑agnostic** – use in‑process queues, WebSocket, or any custom transport.
- **Scalable** – supports multiple agents of the same type with round‑robin distribution (via [neural‑hub](https://github.com/firecode16/neural-hub)).

---

## Core Concepts

| Concept               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **NeuralSignal**      | A binary packet containing a signal type, source/target IDs, and a JSON payload. |
| **NeuralSignalType**  | Digital neurotransmitters: `ACTION_POTENTIAL`, `DOPAMINE`, `SEROTONIN`, `NOREPINEPHRINE`, `GABA`, `GLUTAMATE`. |
| **NeuralIdentity**    | Unique SHA‑256 based identifier for every agent.                           |
| **Synapse**           | A directed connection between two agents that strengthens/weakens with success/failure (Hebbian learning). |
| **Transport**         | Pluggable layer for message delivery – `LocalTransport` (asyncio.Queue) and `WebSocket` client included. |

---

## Installation

```bash
pip install neural-protocol
```

Or install from source:

```bash
git clone https://github.com/firecode16/neural-protocol.git
cd neural-protocol
pip install -e .
```

---

## Quick Start

### 1. Local transport (in‑process queues)

```python
import asyncio
from neural_protocol import LocalTransport, NeuralAgent
from neural_protocol.core.signal import NeuralSignal, NeuralSignalType
from neural_protocol.core.identity import NeuralIdentity

class EchoAgent(NeuralAgent):
    async def handle_signal(self, signal):
        print(f"Received: {signal}")

async def main():
    transport = LocalTransport()
    agent = EchoAgent("echo", transport)
    await agent.start()

    # Send a signal to yourself (broadcast would use target="")
    await agent.transport.send(NeuralSignal(
        signal_type=NeuralSignalType.DOPAMINE,
        source=agent.identity.neural_hash,
        target=agent.identity.neural_hash,
        payload={"hello": "world"}
    ))
    await asyncio.sleep(0.1)
    await agent.stop()

asyncio.run(main())
```

### 2. WebSocket client (connect to a [neural‑hub](https://github.com/firecode16/neural-hub) server)

```python
from neural_protocol.agent.base_ws import WSNeuralAgent
from neural_protocol.core.signal import NeuralSignalType

class MyAgent(WSNeuralAgent):
    async def handle_signal(self, signal):
        print(f"Got: {signal}")

async def main():
    agent = MyAgent("worker", hub_host="127.0.0.1", hub_port=8765)
    await agent.start()
    await agent.transmit("coordinator", NeuralSignalType.NOREPINEPHRINE, {"task": "process"})
    await asyncio.sleep(5)
    await agent.stop()
```

---

## Benchmark

| Protocol        | Size (bytes) | vs NeuralProtocol |
|-----------------|--------------|-------------------|
| NeuralProtocol  | 228          | ✅ baseline       |
| REST/JSON       | 513          | 2.2× larger       |
| GraphQL         | 447          | 2.0× larger       |

**Encode + decode speed:**  
100,000 operations in **0.69s** → **~145,000 signals/second**.  
Integrity check passes 100%.

Run the benchmark yourself:

```bash
python -m neural_protocol.demo.benchmark
```

---

## Built‑in Agents (Demo)

The library includes three example agents that showcase a realistic customer‑support flow:

- `SupportAgent` – receives tickets, detects upsell opportunities.
- `SalesAgent` – creates deals, applies discounts.
- `BillingAgent` – processes payments, broadcasts dopamine.

They can run locally (with `LocalTransport`) or connect to a neural‑hub via WebSocket (using `WSSupportAgent` etc.).  
Try the demo:

```bash
# Local in‑process demo
python -m neural_protocol.demo.run_demo

# WebSocket demo (requires a running neural‑hub)
python -m neural_protocol.demo.run_hub_demo
```

---

## Creating Custom Agents

You can inherit from `NeuralAgent` (for any transport) or `WSNeuralAgent` (for WebSocket).  
Override `handle_signal` and optionally use the `on_signal` decorator.

```python
from neural_protocol.agent.base_ws import WSNeuralAgent
from neural_protocol.core.signal import NeuralSignalType

class MyAnalyticsAgent(WSNeuralAgent):
    def __init__(self, **kwargs):
        super().__init__("analytics", **kwargs)

    @WSNeuralAgent.on_signal(NeuralSignalType.DOPAMINE)
    async def on_reward(self, signal):
        print(f"Reward received: {signal.payload}")
```

---

## Transports

- **`LocalTransport`** – in‑process queues, perfect for testing and single‑process systems.
- **`WebSocket` client** – connects to a neural‑hub server. Supports SSL (WSS) with auto‑reconnect and round‑robin distribution when multiple agents share the same name.
- **Custom transports** – implement the `Transport` abstract base class and inject it into `NeuralAgent`.

---

## Using Neural‑Hub

For distributed agents across multiple machines or processes, you need the [neural‑hub](https://github.com/firecode16/neural-hub) server.  
It acts as a central registry, router, and synaptic database.

- Agents connect via WebSocket (or WSS in production).
- The hub handles message delivery, offline queuing, and synaptic plasticity.
- Round‑robin distribution is automatic when sending to a logical name (e.g., `"ventas"`).

Install neural‑hub separately:

```bash
pip install neural-hub
# Start the hub
neural-hub --port 8765
```

Then connect agents using `WSNeuralAgent` as shown above.

---

## Development & Testing

Run tests:

```bash
python -m unittest discover tests
```

Format code with [Black](https://github.com/psf/black):

```bash
black neural_protocol/ tests/
```

---

## License

MIT © 2025 Firecode16

---

**Inspired by the brain – built for AI agents.**  
Try it, extend it, and join the conversation!
```
