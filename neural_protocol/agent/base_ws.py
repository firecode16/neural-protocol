"""
WebSocket-based Neural Agent that connects directly to a NeuralHub.
This agent does not use a Transport; it communicates directly with the hub.
Now with support for round-robin and optional SSL (WSS).
"""
import asyncio
import ssl
import time
from typing import Dict, List, Optional, Callable, Union

from ..core.signal import NeuralSignal, NeuralSignalType
from ..core.identity import NeuralIdentity
from ..core.synapse import Synapse
from ..transport.websocket import (
    connect_websocket,
    WebSocketConnection,
    ctrl_msg,
    parse_ctrl,
    is_ctrl,
    create_dev_ssl_context,
)


class WSNeuralAgent:
    """
    Agente del NeuralProtocol que se comunica con un Hub vía WebSocket.
    
    Uso:
        agent = WSNeuralAgent("soporte", hub_host="127.0.0.1", hub_port=8765)
        await agent.start()
        await agent.transmit("ventas", NeuralSignalType.NOREPINEPHRINE, {...})
        
    Para usar WSS (WebSocket Secure):
        agent = WSNeuralAgent("soporte", hub_host="127.0.0.1", hub_port=8765, use_ssl=True)
        # o pasar un contexto SSL personalizado:
        # agent = WSNeuralAgent(..., ssl_context=my_ssl_context)
    """

    RECONNECT_BASE_DELAY = 1.0   # segundos
    RECONNECT_MAX_DELAY  = 30.0

    def __init__(
        self,
        agent_id: str,
        hub_host: str = "127.0.0.1",
        hub_port: int = 8765,
        use_ssl: Union[bool, ssl.SSLContext, None] = None,
    ) -> None:
        """
        :param use_ssl: 
            - True: usa un contexto SSL para desarrollo (certificados no validados)
            - SSLContext: usa ese contexto específico
            - None o False: conexión sin SSL (ws://)
        """
        self.identity = NeuralIdentity.generate(agent_id)
        self.hub_host = hub_host
        self.hub_port = hub_port
        self.use_ssl = use_ssl

        self._conn: Optional[WebSocketConnection] = None
        self._peers: Dict[str, str] = {}       # agent_id → neural_hash (para resolución local, aún útil para algunos casos)
        self._synapses: Dict[str, Synapse] = {} # target_hash → Synapse (solo para tracking local)
        self._memory: List[NeuralSignal] = []
        self._handlers: Dict[NeuralSignalType, Callable] = {}
        self._running = False
        self._connected = asyncio.Event()
        self._log: List[str] = []
        self._reconnect_attempts = 0

    # ── Arranque y conexión ───────────────────────────────────────────────

    async def start(self) -> None:
        """Conecta al Hub y arranca el loop de recepción en background."""
        self._running = True
        asyncio.create_task(self._connection_loop())
        # Esperar conexión inicial antes de retornar
        await asyncio.wait_for(self._connected.wait(), timeout=15.0)

    async def stop(self) -> None:
        self._running = False
        if self._conn:
            await self._conn.close()
        self._info("🔴 Offline")

    async def _connection_loop(self) -> None:
        """Loop de conexión con reconexión automática y backoff exponencial."""
        while self._running:
            try:
                await self._connect_and_register()
                self._reconnect_attempts = 0
                await self._receive_loop()
            except Exception as e:
                self._info(f"⚠️  Desconectado: {e}")

            if not self._running:
                break

            self._connected.clear()
            delay = min(
                self.RECONNECT_BASE_DELAY * (2 ** self._reconnect_attempts),
                self.RECONNECT_MAX_DELAY,
            )
            self._reconnect_attempts += 1
            self._info(f"🔄 Reconectando en {delay:.1f}s...")
            await asyncio.sleep(delay)

    async def _connect_and_register(self) -> None:
        """Establece WebSocket y completa registro con el Hub."""
        proto = "wss" if self.use_ssl else "ws"
        self._info(f"🔌 Conectando a Hub {proto}://{self.hub_host}:{self.hub_port}...")
        self._conn = await connect_websocket(
            self.hub_host,
            self.hub_port,
            ssl_param=self.use_ssl,
        )

        # Enviar registro
        await self._conn.send(ctrl_msg(
            "register",
            agent_id=self.identity.agent_id,
            neural_hash=self.identity.neural_hash,
        ))

        # Esperar confirmación
        data = await asyncio.wait_for(self._conn.recv(), timeout=10.0)
        if data is None:
            raise ConnectionError("Hub cerró conexión durante registro")

        ctrl = parse_ctrl(data)
        if ctrl.get("_ctrl") != "registered":
            raise ConnectionError(f"Registro rechazado: {ctrl}")

        # Poblar directorio de peers (útil para descubrimiento, aunque ahora el hub hará balanceo)
        self._peers = ctrl.get("peers", {})
        self._info(
            f"✅ Registrado en Hub | hash={self.identity.neural_hash[:8]} "
            f"| peers={list(self._peers.keys())}"
        )
        self._connected.set()

    async def _receive_loop(self) -> None:
        """Recibe mensajes del Hub (señales entrantes + control)."""
        while self._running and self._conn and not self._conn.closed:
            data = await self._conn.recv()
            if data is None:
                break

            if is_ctrl(data):
                await self._handle_ctrl(parse_ctrl(data))
            else:
                try:
                    signal = NeuralSignal.decode(data)
                    self._memory.append(signal)
                    await self.handle_signal(signal)
                except Exception as e:
                    self._info(f"❌ Error procesando señal: {e}")

    # ── Control messages desde Hub ────────────────────────────────────────

    async def _handle_ctrl(self, ctrl: dict) -> None:
        t = ctrl.get("_ctrl")
        if t == "peer_joined":
            self._peers[ctrl["agent_id"]] = ctrl["neural_hash"]
            self._info(f"👋 Peer conectado: {ctrl['agent_id']}")
        elif t == "peer_left":
            self._peers.pop(ctrl.get("agent_id", ""), None)
            self._info(f"👋 Peer desconectado: {ctrl.get('agent_id')}")
        elif t == "discover_result":
            # Resultado de auto-descubrimiento (podría ignorarse)
            pass
        elif t == "pong":
            pass  # heartbeat OK

    # ── Transmisión ───────────────────────────────────────────────────────

    async def transmit(
        self,
        target_name: str,
        signal_type: NeuralSignalType,
        payload: Dict,
    ) -> bool:
        """
        Envía señal neural al agente destino a través del Hub.
        El target_name es un nombre lógico (ej. "ventas") y el Hub hará round-robin.
        """
        if not self._connected.is_set():
            self._info(f"⚠️  Sin conexión al Hub, esperando...")
            await asyncio.wait_for(self._connected.wait(), timeout=10.0)

        # Ya no resolvemos el nombre localmente; el hub lo hará.
        # Construimos la señal con target = target_name (nombre, no hash)
        signal = NeuralSignal(
            signal_type=signal_type,
            source=self.identity.neural_hash,
            target=target_name,  # ← ahora enviamos el nombre directamente
            payload=payload,
        )

        self._info(f"📤 {signal} (a nombre '{target_name}')")

        try:
            await self._conn.send(signal.encode())
            self._memory.append(signal)
            # No actualizamos sinapsis local porque el hub las gestiona centralizadamente
            # Pero opcionalmente podemos trackear el intento localmente
            return True

        except Exception as e:
            self._info(f"❌ Error transmitiendo: {e}")
            return False

    async def broadcast(
        self, signal_type: NeuralSignalType, payload: Dict
    ) -> bool:
        """Broadcast a todos los agentes de la red (vía Hub)."""
        if not self._connected.is_set():
            return False

        signal = NeuralSignal(
            signal_type=signal_type,
            source=self.identity.neural_hash,
            target="",  # target vacío = broadcast
            payload=payload,
        )
        self._info(f"📡 BROADCAST {signal.signal_type.name}")
        try:
            await self._conn.send(signal.encode())
            return True
        except Exception:
            return False

    # ── Auto-descubrimiento (opcional, ya no necesario para envío) ────────

    async def _resolve(self, name: str) -> Optional[str]:
        """Resuelve nombre a hash (ya no se usa en transmit, pero puede ser útil para otros fines)."""
        if name in self._peers:
            return self._peers[name]
        return None

    # ── Override en subclases ─────────────────────────────────────────────

    async def handle_signal(self, signal: NeuralSignal) -> None:
        """Override para manejar señales entrantes."""
        handler = self._handlers.get(signal.signal_type)
        if handler:
            await handler(signal)
        else:
            self._info(
                f"📥 {signal.signal_type.emoji()} {signal.signal_type.name} "
                f"de {signal.source[:8]}"
            )

    def on_signal(self, signal_type: NeuralSignalType) -> Callable:
        """Decorador para registrar handlers."""
        def decorator(fn):
            self._handlers[signal_type] = fn
            return fn
        return decorator

    # ── Utilidades ────────────────────────────────────────────────────────

    def synapse_report(self) -> str:
        if not self._synapses:
            return "  (sin sinapsis)"
        return "\n".join(f"  {syn}" for syn in self._synapses.values())

    def _info(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {self.identity.agent_id:12s} | {msg}"
        self._log.append(line)
        print(line)