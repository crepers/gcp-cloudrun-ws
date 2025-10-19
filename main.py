#!/usr/bin/env python

import asyncio
import websockets
import os
import time
from http import HTTPStatus

# OpenTelemetry API for instrumenting code
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter

from opentelemetry.sdk.metrics import MeterProvider

# Set up OpenTelemetry Metrics SDK
# Google Cloud Monitoring Exporter를 사용하도록 설정합니다.
# 이 Exporter는 메트릭을 주기적으로 Cloud Monitoring API로 직접 전송합니다.
# --- OpenTelemetry Metrics Setup ---
# Set up a meter provider
metric_reader = PeriodicExportingMetricReader(
    CloudMonitoringMetricsExporter()
)
meter_provider = MeterProvider(metric_readers=[metric_reader])

# Get a meter for this module
meter = meter_provider.get_meter("websocket.echo.server")

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

async def echo(websocket, path): # path 인자를 유지합니다.
    """Handles a single WebSocket connection, echoing messages and recording metrics."""
    # Track connection lifecycle and metrics
    start_time = time.monotonic()
    connections_total.add(1)
    active_connections.add(1)
    print(f"New connection from path: {path}", flush=True)
    try:
        async for message in websocket:
            print("Received and echoing message: " + str(message), flush=True)
            messages_received.add(1)
            try:
                # 메시지 크기를 기록합니다. (str, bytes 모두 처리)
                message_size_bytes.record(len(message))
            except TypeError:
                pass
            await websocket.send(message)
            messages_sent.add(1)
    finally:
        duration = time.monotonic() - start_time
        connection_duration.record(duration)
        active_connections.add(-1)
        print("Connection closed", flush=True)

async def http_handler(path, request_headers):
    """Handles plain HTTP requests for health checks."""
    if "Upgrade" not in request_headers or request_headers["Upgrade"].lower() != "websocket":
        # Cloud Run 헬스 체크 또는 다른 HTTP 요청에 대해 간단한 OK를 반환합니다.
        return HTTPStatus.OK, [], b"OK"

    # WebSocket 핸드셰이크는 websockets 라이브러리가 처리하도록 None을 반환합니다.
    return None

async def main():
    """Starts the WebSocket server with an HTTP handler."""
    port = int(os.environ.get('PORT', 8080))
    async with websockets.serve(echo, '0.0.0.0', port, process_request=http_handler):
        print(f"Server is running on port {port}", flush=True)
        await asyncio.Future()  # 서버를 계속 실행합니다.

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server has been stopped.")
