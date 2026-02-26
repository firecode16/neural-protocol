#!/usr/bin/env python3
"""Benchmark NeuralProtocol vs REST/JSON."""
import json
import time
from ..core.signal import NeuralSignal, NeuralSignalType

def run_benchmark():
    signal = NeuralSignal(
        signal_type=NeuralSignalType.NOREPINEPHRINE,
        source="soporte_abc123",
        target="ventas_def456",
        payload={
            "ticket_id": "TKT-001",
            "customer": "customer_123",
            "issue": "Mi aplicación va muy lenta",
            "opportunity": "storage_expansion",
            "estimated_value": 199.99,
            "urgency": "high",
        },
    )

    neural_bytes = signal.encode()

    rest_equivalent = {
        "method": "POST",
        "path": "/api/v1/opportunities",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9...",
            "X-Agent-ID": "soporte_abc123",
            "X-Request-ID": signal.msg_id,
        },
        "body": {
            "ticket_id": "TKT-001",
            "customer_id": "customer_123",
            "issue_description": "Mi aplicación va muy lenta",
            "opportunity_type": "storage_expansion",
            "estimated_value": 199.99,
            "priority": "high",
            "source_agent": "soporte_abc123",
            "target_agent": "ventas_def456",
            "timestamp": signal.timestamp,
        }
    }
    rest_bytes = json.dumps(rest_equivalent, separators=(",", ":")).encode()

    graphql_equivalent = {
        "query": "mutation CreateOpportunity($input: OpportunityInput!) { createOpportunity(input: $input) { id status } }",
        "variables": rest_equivalent["body"],
        "operationName": "CreateOpportunity"
    }
    graphql_bytes = json.dumps(graphql_equivalent, separators=(",", ":")).encode()

    print("\n{:<20} {:<15} {}".format("Protocolo", "Tamaño", "vs NeuralProtocol"))
    print("-"*50)
    print(f"{'NeuralProtocol':<20} {len(neural_bytes):<15} ✅ Baseline")
    print(f"{'REST/JSON':<20} {len(rest_bytes):<15} {len(rest_bytes)/len(neural_bytes):.1f}x más grande")
    print(f"{'GraphQL':<20} {len(graphql_bytes):<15} {len(graphql_bytes)/len(neural_bytes):.1f}x más grande")

    N = 100_000
    t0 = time.perf_counter()
    for _ in range(N):
        NeuralSignal.decode(signal.encode())
    elapsed = time.perf_counter() - t0

    print(f"\n⚡ Encode+Decode: {N:,} ops en {elapsed:.3f}s")
    print(f"   → {N/elapsed:,.0f} señales/seg")
    print(f"   → {elapsed/N*1000:.4f} ms por señal")

    decoded = NeuralSignal.decode(neural_bytes)
    assert decoded.signal_type == signal.signal_type
    assert decoded.payload == signal.payload
    assert decoded.source == signal.source
    print("✅ Integridad verificada")


if __name__ == "__main__":
    run_benchmark()