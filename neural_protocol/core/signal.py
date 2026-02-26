"""
NeuralProtocol Core - Signal definitions.
"""
import json
import struct
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict

MAGIC = b"NP"
VERSION = 1
HEADER_FMT = "!2sBBd16sBBI"

class NeuralSignalType(IntEnum):
    ACTION_POTENTIAL = 0
    DOPAMINE = 1
    SEROTONIN = 2
    NOREPINEPHRINE = 3
    GABA = 4
    GLUTAMATE = 5

    def emoji(self) -> str:
        return {0: "⚡", 1: "🟢", 2: "🔵", 3: "🟡", 4: "🔴", 5: "🟣"}[self.value]

    def description(self) -> str:
        return {
            0: "Activación",
            1: "Recompensa",
            2: "Estabilización",
            3: "Alerta/Oportunidad",
            4: "Inhibición",
            5: "Excitación/Aprendizaje",
        }[self.value]


@dataclass
class NeuralSignal:
    signal_type: NeuralSignalType
    source: str
    target: str
    payload: Dict[str, Any]
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)
    ttl: int = 10

    def encode(self) -> bytes:
        payload_bytes = json.dumps(self.payload, separators=(",", ":")).encode()
        src_bytes = self.source.encode()
        tgt_bytes = self.target.encode()
        msg_id_bytes = bytes.fromhex(self.msg_id.ljust(32, "0")[:32])

        header = struct.pack(
            HEADER_FMT,
            MAGIC,
            VERSION,
            int(self.signal_type),
            self.timestamp,
            msg_id_bytes,
            len(src_bytes),
            len(tgt_bytes),
            len(payload_bytes),
        )
        return header + src_bytes + tgt_bytes + payload_bytes

    @classmethod
    def decode(cls, data: bytes) -> "NeuralSignal":
        hdr_size = struct.calcsize(HEADER_FMT)
        (magic, version, sig_type, timestamp,
         msg_id_bytes, src_len, tgt_len, payload_len) = struct.unpack(
            HEADER_FMT, data[:hdr_size]
        )
        if magic != MAGIC:
            raise ValueError(f"Invalid magic: {magic!r}")

        offset = hdr_size
        source = data[offset: offset + src_len].decode()
        offset += src_len
        target = data[offset: offset + tgt_len].decode()
        offset += tgt_len
        payload = json.loads(data[offset: offset + payload_len].decode())

        return cls(
            signal_type=NeuralSignalType(sig_type),
            source=source,
            target=target,
            payload=payload,
            msg_id=msg_id_bytes.hex(),
            timestamp=timestamp,
        )

    def size_bytes(self) -> int:
        return len(self.encode())

    def __str__(self) -> str:
        sig = self.signal_type
        return (
            f"{sig.emoji()} NeuralSignal [{sig.name}] "
            f"{self.source[:8]}→{self.target[:8] or 'BROADCAST'} "
            f"| {self.size_bytes()}B | payload_keys={list(self.payload.keys())}"
        )