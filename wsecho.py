#!/usr/bin/env python

import asyncio
import websockets
import os
import time
from http import HTTPStatus

# OpenTelemetry API for instrumenting code
from opentelemetry import metrics
# OpenTelemetry SDK for configuring the API
from opentelemetry.sdk.metrics import MeterProvider
# Prometheus Exporter to export metrics to Prometheus
from opentelemetry.exporter.prometheus import PrometheusMetricReader

# Set up OpenTelemetry Metrics SDK
# A reader is where exporters are registered.
# A reader is responsible for collecting and exporting metrics.
# We use the PrometheusMetricReader to export metrics to Prometheus.
reader = PrometheusMetricReader()
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)

# Get a meter from the MeterProvider
meter = metrics.get_meter("websocket.echo.server")

# Create instruments (metrics)
connections_total = meter.create_counter(
    "websocket_connections_total",
    description="Total number of websocket connections started",
)
active_connections = meter.create_up_down_counter(
    "websocket_active_connections",
    description="Number of active websocket connections",
)
messages_received = meter.create_counter(
    "websocket_messages_received_total",
    description="Total number of messages received",
)
messages_sent = meter.create_counter(
    "websocket_messages_sent_total",
    description="Total number of messages sent",
)
message_size_bytes = meter.create_histogram(
    "websocket_message_size_bytes",
    unit="By",
    description="Histogram of message sizes in bytes",
)
connection_duration = meter.create_histogram(
    "websocket_connection_duration_seconds",
    unit="s",
    description="Connection duration in seconds",
)


async def echo(websocket):
    # Track connection lifecycle and metrics
    start = time.monotonic()
    connections_total.add(1)
    active_connections.add(1)
    try:
        async for message in websocket:
            print("Received and echoing message: " + message, flush=True)
            messages_received.add(1)
            try:
                message_size_bytes.record(len(message))
            except Exception:
                # message might not be a sized object in some edge cases
                pass
            await websocket.send(message)
            messages_sent.add(1)
    finally:
        duration = time.monotonic() - start
        connection_duration.record(duration)
        active_connections.add(-1)


async def http_handler(path):
    """Handle plain HTTP requests on the same port as the websocket server."""
    if path == '/':
        try:
            with open('static/index.html', 'r') as f:
                return HTTPStatus.OK, [('Content-Type', 'text/html')], f.read()
        except FileNotFoundError:
            return HTTPStatus.NOT_FOUND, [], "Not Found"
    # Returning None delegates to the normal WebSocket handshake/handling for other paths
    return None


async def main():
    """Starts the WebSocket server."""
    port = int(os.environ.get('PORT', 8080))

    # The 'async with' statement ensures the server is properly shut down.
    async with websockets.serve(echo, '0.0.0.0', port, process_request=http_handler):
        print(f"WebSocket server is running on port {port}")
        await asyncio.Future()  # This will run the server indefinitely

if __name__ == "__main__":
    # asyncio.run() starts the event loop and runs the main() coroutine.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server has been stopped.")
