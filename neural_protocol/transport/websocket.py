"""
WebSocket RFC 6455 — Implementación pura en stdlib Python
==========================================================
Sin dependencias externas. Implementa:
  - Handshake HTTP → WebSocket upgrade
  - Framing / unframing de mensajes (texto y binario)
  - Ping/Pong keepalive
  - Close frame
  - Servidor y cliente async con asyncio
  - Soporte SSL/TLS (WSS)

Referencia: https://datatracker.ietf.org/doc/html/rfc6455
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import struct
import os
import json
import ssl
from enum import IntEnum
from typing import Optional, Callable, Awaitable, Union


# ─────────────────────────────────────────────
# OPCODES RFC 6455
# ─────────────────────────────────────────────

class Opcode(IntEnum):
    CONTINUATION = 0x0
    TEXT         = 0x1
    BINARY       = 0x2
    CLOSE        = 0x8
    PING         = 0x9
    PONG         = 0xA


# ─────────────────────────────────────────────
# FRAMING (Serialización de mensajes WS)
# ─────────────────────────────────────────────

def build_frame(payload: bytes, opcode: Opcode = Opcode.BINARY, mask: bool = False) -> bytes:
    """
    Construye un frame WebSocket RFC 6455.

    Estructura:
      Byte 0: FIN(1) + RSV(3) + Opcode(4)
      Byte 1: MASK(1) + Payload_len(7)
      [Extended len: 2 o 8 bytes si len > 125]
      [Masking key: 4 bytes si MASK=1]
      Payload
    """
    fin_opcode = 0x80 | int(opcode)   # FIN=1 siempre (no fragmentamos)
    length = len(payload)

    # Payload length encoding
    if length <= 125:
        len_byte = length
        ext_len = b""
    elif length <= 65535:
        len_byte = 126
        ext_len = struct.pack("!H", length)
    else:
        len_byte = 127
        ext_len = struct.pack("!Q", length)

    if mask:
        len_byte |= 0x80
        masking_key = os.urandom(4)
        masked_payload = bytes(
            b ^ masking_key[i % 4] for i, b in enumerate(payload)
        )
        return bytes([fin_opcode, len_byte]) + ext_len + masking_key + masked_payload
    else:
        return bytes([fin_opcode, len_byte]) + ext_len + payload


def parse_frame(data: bytes) -> tuple[Optional[Opcode], bytes, int]:
    """
    Parsea un frame WebSocket desde bytes crudos.
    
    Retorna: (opcode, payload, bytes_consumed)
    Si el frame está incompleto retorna (None, b"", 0)
    """
    if len(data) < 2:
        return None, b"", 0

    fin  = (data[0] & 0x80) != 0
    opcode = Opcode(data[0] & 0x0F)
    masked = (data[1] & 0x80) != 0
    length = data[1] & 0x7F

    offset = 2

    # Extended length
    if length == 126:
        if len(data) < offset + 2:
            return None, b"", 0
        length = struct.unpack("!H", data[offset:offset+2])[0]
        offset += 2
    elif length == 127:
        if len(data) < offset + 8:
            return None, b"", 0
        length = struct.unpack("!Q", data[offset:offset+8])[0]
        offset += 8

    # Masking key
    if masked:
        if len(data) < offset + 4:
            return None, b"", 0
        masking_key = data[offset:offset+4]
        offset += 4

    # Payload
    if len(data) < offset + length:
        return None, b"", 0

    payload = data[offset:offset+length]
    if masked:
        payload = bytes(b ^ masking_key[i % 4] for i, b in enumerate(payload))

    return opcode, payload, offset + length


# ─────────────────────────────────────────────
# HANDSHAKE HTTP → WebSocket
# ─────────────────────────────────────────────

WS_MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def compute_accept_key(client_key: str) -> str:
    """Calcula el Sec-WebSocket-Accept según RFC 6455."""
    combined = client_key.strip() + WS_MAGIC
    sha1 = hashlib.sha1(combined.encode()).digest()
    return base64.b64encode(sha1).decode()

def build_handshake_response(client_key: str) -> bytes:
    accept = compute_accept_key(client_key)
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        "\r\n"
    )
    return response.encode()

def parse_http_request(data: bytes) -> dict:
    """Parsea request HTTP de upgrade, retorna headers."""
    text = data.decode(errors="replace")
    lines = text.split("\r\n")
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()
    return headers

def build_client_handshake(host: str, port: int, path: str = "/") -> tuple[bytes, str]:
    """Construye HTTP upgrade request para cliente WS."""
    key_bytes = os.urandom(16)
    key = base64.b64encode(key_bytes).decode()
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )
    return request.encode(), key


# ─────────────────────────────────────────────
# WEBSOCKET CONNECTION
# ─────────────────────────────────────────────

class WebSocketConnection:
    """
    Conexión WebSocket bidireccional sobre asyncio streams.
    Funciona tanto para el lado servidor como cliente.
    """

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        is_client: bool = False,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.is_client = is_client   # Clientes deben enmascarar (RFC 6455 §5.3)
        self._buffer = b""
        self._closed = False
        self.remote_addr = writer.get_extra_info("peername", ("?", 0))

    async def send(self, data: bytes) -> None:
        """Envía datos binarios como un frame WebSocket."""
        if self._closed:
            raise ConnectionError("Conexión cerrada")
        frame = build_frame(data, opcode=Opcode.BINARY, mask=self.is_client)
        self.writer.write(frame)
        await self.writer.drain()

    async def recv(self) -> Optional[bytes]:
        """
        Recibe el siguiente mensaje completo.
        Maneja automáticamente PING/PONG y CLOSE.
        Retorna None si la conexión se cerró.
        """
        while True:
            # Intentar parsear buffer acumulado
            opcode, payload, consumed = parse_frame(self._buffer)

            if consumed == 0:
                # Necesitamos más datos
                try:
                    chunk = await asyncio.wait_for(
                        self.reader.read(4096), timeout=30.0
                    )
                    if not chunk:
                        self._closed = True
                        return None
                    self._buffer += chunk
                    continue
                except asyncio.TimeoutError:
                    await self._send_ping()
                    continue
                except Exception:
                    self._closed = True
                    return None

            self._buffer = self._buffer[consumed:]

            if opcode == Opcode.BINARY or opcode == Opcode.TEXT:
                return payload
            elif opcode == Opcode.PING:
                await self._send_pong(payload)
            elif opcode == Opcode.PONG:
                pass  # keepalive OK
            elif opcode == Opcode.CLOSE:
                await self._send_close()
                self._closed = True
                return None

    async def _send_ping(self) -> None:
        frame = build_frame(b"ping", opcode=Opcode.PING, mask=self.is_client)
        self.writer.write(frame)
        await self.writer.drain()

    async def _send_pong(self, payload: bytes) -> None:
        frame = build_frame(payload, opcode=Opcode.PONG, mask=self.is_client)
        self.writer.write(frame)
        await self.writer.drain()

    async def _send_close(self) -> None:
        frame = build_frame(b"", opcode=Opcode.CLOSE, mask=self.is_client)
        self.writer.write(frame)
        await self.writer.drain()

    async def close(self) -> None:
        if not self._closed:
            await self._send_close()
            self._closed = True
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass

    @property
    def closed(self) -> bool:
        return self._closed


# ─────────────────────────────────────────────
# SERVIDOR WebSocket (con soporte SSL)
# ─────────────────────────────────────────────

HandlerFn = Callable[[WebSocketConnection], Awaitable[None]]

async def serve_websocket(
    handler: HandlerFn,
    host: str = "0.0.0.0",
    port: int = 8765,
    ssl: Optional[ssl.SSLContext] = None,
) -> asyncio.AbstractServer:
    """
    Inicia un servidor WebSocket.
    Por cada conexión nueva llama a handler(conn).
    Si se proporciona ssl_context, se usa WSS.
    """

    async def _handle_raw(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        # Leer HTTP upgrade request
        raw = b""
        while b"\r\n\r\n" not in raw:
            chunk = await reader.read(1024)
            if not chunk:
                writer.close()
                return
            raw += chunk

        headers = parse_http_request(raw)
        ws_key = headers.get("sec-websocket-key")

        if not ws_key or headers.get("upgrade", "").lower() != "websocket":
            writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            writer.close()
            return

        # Completar handshake
        writer.write(build_handshake_response(ws_key))
        await writer.drain()

        conn = WebSocketConnection(reader, writer, is_client=False)
        await handler(conn)

    server = await asyncio.start_server(_handle_raw, host, port, ssl=ssl)
    return server


# ─────────────────────────────────────────────
# CLIENTE WebSocket (con soporte SSL)
# ─────────────────────────────────────────────

def create_dev_ssl_context() -> ssl.SSLContext:
    """Crea un contexto SSL que no valida certificados (para desarrollo con WSS)."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context

async def connect_websocket(
    host: str,
    port: int,
    path: str = "/",
    retries: int = 5,
    retry_delay: float = 1.0,
    ssl_param: Union[bool, ssl.SSLContext, None] = None,  # Cambiado de 'ssl' a 'ssl_param'
) -> WebSocketConnection:
    """
    Conecta como cliente WebSocket con reintentos automáticos.
    
    - ssl_param = True: usa un contexto para desarrollo (sin validar certificado).
    - ssl_param = SSLContext: usa ese contexto.
    - ssl_param = None: conexión sin SSL (ws://).
    """
    ssl_context = None
    if ssl_param is True:
        ssl_context = create_dev_ssl_context()
    elif isinstance(ssl_param, ssl.SSLContext):
        ssl_context = ssl_param

    last_err = None
    for attempt in range(retries):
        try:
            reader, writer = await asyncio.open_connection(host, port, ssl=ssl_context)

            # Enviar HTTP upgrade
            request, key = build_client_handshake(host, port, path)
            writer.write(request)
            await writer.drain()

            # Leer respuesta del servidor
            response = b""
            while b"\r\n\r\n" not in response:
                chunk = await reader.read(1024)
                if not chunk:
                    raise ConnectionError("Servidor cerró conexión durante handshake")
                response += chunk

            # Verificar 101 Switching Protocols
            if b"101" not in response:
                raise ConnectionError(f"Handshake rechazado: {response[:100]}")

            return WebSocketConnection(reader, writer, is_client=True)

        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))

    raise ConnectionError(f"No se pudo conectar después de {retries} intentos: {last_err}")


# ─────────────────────────────────────────────
# MENSAJES DE CONTROL (JSON)
# ─────────────────────────────────────────────

def ctrl_msg(type_: str, **kwargs) -> bytes:
    return json.dumps({"_ctrl": type_, **kwargs}).encode()

def is_ctrl(data: bytes) -> bool:
    try:
        return b'"_ctrl"' in data
    except Exception:
        return False

def parse_ctrl(data: bytes) -> dict:
    return json.loads(data)