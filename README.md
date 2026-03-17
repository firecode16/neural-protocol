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
- **Federated (Fase 2)** – agents can communicate across different hubs using global identifiers (`nombre@dominio`).  
  *Now with dynamic discovery and presence tracking between hubs.*
- **JSON‑RPC 2.0 ready** – agents can act as JSON‑RPC clients to query hub status, discover agents, check remote availability, or transmit signals programmatically.

---

## Core Concepts

| Concept               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **NeuralSignal**      | A binary packet containing a signal type, source/target IDs, and a JSON payload. |
| **NeuralSignalType**  | Digital neurotransmitters: `ACTION_POTENTIAL`, `DOPAMINE`, `SEROTONIN`, `NOREPINEPHRINE`, `GABA`, `GLUTAMATE`. |
| **NeuralIdentity**    | Unique SHA‑256 based identifier for every agent. Now includes an optional **domain** for global identification (`agent_id@domain`). |
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

## 📡 JSON‑RPC 2.0 Client Capabilities

`WSNeuralAgent` includes a built‑in JSON‑RPC 2.0 client that allows you to interact with the hub programmatically.

### Methods

#### `jsonrpc_call(method, params=None, timeout=10.0)`

Sends a JSON‑RPC request and waits for the correlated response.

```python
# Get hub status
status = await agent.jsonrpc_call("hub.status")
print(f"Agents online: {status['agents_online']}")

# Discover an agent by name
info = await agent.jsonrpc_call("agent.discover", {"name": "ventas"})
print(f"Agent hash: {info['neural_hash']}, online: {info['online']}")

# Transmit a signal via JSON‑RPC
result = await agent.jsonrpc_call(
    "agent.transmit",
    {
        "target": "billing",
        "signal_type": "ACTION_POTENTIAL",
        "payload": {"invoice_id": 42}
    }
)
print(f"Delivered, msg_id: {result['msg_id']}")

# NEW: Check remote agent availability (requires federation Fase 2)
remote = await agent.jsonrpc_call("remote_agent.discover", {"name": "vendedor@empresa-b.com"})
if remote["online"]:
    print("Remote agent is online")
```

#### `jsonrpc_notify(method, params=None)`

Sends a JSON‑RPC notification (no response expected). Ideal for events, telemetry, or fire‑and‑forget commands.

```python
# Send a ping notification (hub won't reply)
await agent.jsonrpc_notify("agent.ping", {"source": "monitor"})
```

### Error Handling & Robustness

- **Timeouts**: `jsonrpc_call` raises `asyncio.TimeoutError` if no response arrives within the timeout.
- **Connection loss**: If the WebSocket disconnects, all pending RPC futures are automatically cancelled with a `ConnectionError`. This prevents hanging coroutines.
- **Hub errors**: JSON‑RPC errors (e.g., method not found, invalid params) are raised as `RuntimeError` with the error code and message.

```python
try:
    result = await agent.jsonrpc_call("unknown.method", timeout=5)
except RuntimeError as e:
    print(f"RPC failed: {e}")  # e.g., "JSON‑RPC error -32601: Method not found"
except asyncio.TimeoutError:
    print("Hub did not respond in time")
except ConnectionError:
    print("Agent is offline")
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

## 🌐 Federated Communication (Fase 2)

NeuralProtocol supports **federated multi‑hub architectures**, enabling agents from different domains to communicate seamlessly.  
With **Fase 2**, hubs now exchange real‑time information about available agents, allowing optimized routing and presence checks.

### Key additions for federation

- **Global identifiers**: Agents can be created with a `domain` parameter, resulting in a global ID like `agent_id@domain`.
- **Control message types**: `FWD_SIGNAL`, `HUB_REGISTER`, `HUB_PEER_UPDATE` (dynamic peer updates).
- **Automatic routing**: When an agent calls `transmit("nombre@dominio", ...)`, the local hub forwards the signal to the appropriate remote hub, but **only if the remote agent is known and online** (thanks to dynamic discovery).
- **Presence queries**: Agents can now check if a remote agent is available before sending, using JSON‑RPC (`remote_agent.discover`).
- **Backward compatible**: Existing agents without a domain continue to work as before.

### Using federation in your agents

Simply pass the `domain` argument when creating a `WSNeuralAgent`:

```python
agent = MyAgent(
    agent_id="comprador",
    domain="empresa-a.com",
    hub_host="localhost",
    hub_port=8765
)
await agent.start()

# Check if remote agent is online before sending (NEW)
info = await agent.jsonrpc_call("remote_agent.discover", {"name": "vendedor@empresa-b.com"})
if info["online"]:
    await agent.transmit("vendedor@empresa-b.com", NeuralSignalType.NOREPINEPHRINE, {...})
else:
    print("Remote agent is offline, try later")
```

The agent will automatically include its domain during registration, and the hub will handle the rest (including dynamic peer updates).

> **Note**: Federation requires a compatible [neural‑hub](https://github.com/firecode16/neural-hub) version (≥1.2) with remote hubs configured and Fase 2 features enabled.

---

## Transports

- **`LocalTransport`** – in‑process queues, perfect for testing and single‑process systems.
- **`WebSocket` client** – connects to a neural‑hub server. Supports SSL (WSS) with auto‑reconnect and round‑robin distribution when multiple agents share the same name.
- **Custom transports** – implement the `Transport` abstract base class and inject it into `NeuralAgent`.

---

## Using NeuralHub

For distributed agents across multiple machines or processes, you need the [neural‑hub](https://github.com/firecode16/neural-hub) server.  
It acts as a central registry, router, and synaptic database.

- Agents connect via WebSocket (or WSS in production).
- The hub handles message delivery, offline queuing, and synaptic plasticity.
- Round‑robin distribution is automatic when sending to a logical name (e.g., `"ventas"`).
- **Federation (Fase 2)** allows multiple hubs to interconnect with dynamic discovery and presence tracking.
- **JSON‑RPC 2.0 API** – the hub exposes a rich JSON‑RPC interface for monitoring and control (see [neural‑hub README](https://github.com/firecode16/neural-hub) for details).

Install neural‑hub separately:

```bash
pip install neural-hub
# Start the hub
neural-hub --port 8765
```

Then connect agents using `WSNeuralAgent` as shown.

---

## Robustness & Performance

- **Automatic reconnection** – WebSocket clients retry with exponential backoff.
- **Message integrity** – each signal includes a magic number and version; malformed packets are rejected.
- **High throughput** – >140k signals/sec encode/decode.
- **Low memory footprint** – signals are binary, no heavy serialization overhead.
- **Federation overhead** – minimal; forwarded signals are wrapped in a small JSON control message, and peer updates are periodic (every 30s) or event‑driven.
- **JSON‑RPC resilience** – pending RPC futures are automatically cancelled on disconnection, preventing resource leaks.

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

## Roadmap

### ✅ Fase 1: Conexión básica entre hubs (completada)
- Identidad global de agentes (`nombre@dominio`).
- Nuevos tipos de mensajes de control (`FWD_SIGNAL`, `HUB_REGISTER`).
- Soporte en `WSNeuralAgent` para envío a destinos remotos.
- Compatibilidad con [neural‑hub](https://github.com/firecode16/neural-hub) Fase 1.

### ✅ Fase 2: Descubrimiento dinámico y presencia (completada)
- Intercambio de listas de agentes entre hubs (`HUB_PEER_UPDATE`).
- El cliente puede consultar disponibilidad remota antes de enviar (vía JSON‑RPC).
- Optimizaciones de enrutamiento (el hub solo reenvía si el destino existe y está online).

### ⏳ Fase 3: Alta disponibilidad y balanceo (próximo)
- Soporte para múltiples hubs por dominio (clúster).
- Resolución de conflictos de nombres.
- Sincronización de sinapsis entre réplicas.

Contributions and ideas are welcome!

---

## License

MIT © 2026 Firecode16

---

**Inspired by the brain – built for AI agents.**  
Try it, extend it, and join the conversation!
