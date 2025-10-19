# WebSocket Echo Server (Python) with OpenTelemetry

This repository contains a minimal WebSocket echo server written in Python. It is instrumented with **OpenTelemetry** to export metrics directly to **Google Cloud Monitoring**, making it observable and ready for cloud-native environments like Google Cloud Run.

It also includes a simple HTML/JavaScript test client served directly from the application.

## Features

-   WebSocket echo functionality.
-   Metrics exported directly to Google Cloud Monitoring.
-   Instrumented with OpenTelemetry for vendor-neutral observability.
-   Built-in web-based test client.
-   Containerized with a `Dockerfile` for easy deployment.

## Files

-   `main.py`: The main Python server application.
-   `requirements.txt`: Python dependencies (websockets, OpenTelemetry, Google Cloud Exporter).
-   `Dockerfile`: Container image definition.
-   `static/index.html`: A simple web-based client for testing the server.

## Metrics

Metrics are exposed via OpenTelemetry and are compatible with Prometheus.

-   `websocket_connections_total` (Counter): Total number of WebSocket connections started.
-   `websocket_active_connections` (UpDownCounter): Number of active websocket connections.
-   `websocket_messages_received_total` (Counter): Total number of messages received.
-   `websocket_messages_sent_total` (Counter): Total number of messages sent.
-   `websocket_message_size_bytes` (Histogram): Distribution of message sizes in bytes.
-   `websocket_connection_duration_seconds` (Histogram): Distribution of connection durations in seconds.

## Run locally

1.  **Create a virtual environment and install dependencies:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
    > **Note:** On Debian-based systems (like Ubuntu), you may need to install the `venv` package separately if it's not included with your Python installation. You can do this by running:
    > ```bash
    > sudo apt-get update
    > sudo apt-get install python3-venv
    > ```
    > If you are using a specific Python version (e.g., `python3.11`), install the corresponding package (e.g., `python3.11-venv`).

2.  **Run the server:**

    ```bash
    python3 main.py
    ```
    > **Note:** When running locally, metrics are configured to be sent to Google Cloud Monitoring. They will not be accessible locally unless you modify `main.py` to use a different exporter (e.g., `ConsoleMetricExporter`).


    The server will start on `http://localhost:8080`.

3.  **Test the server:**
    -   **Web Client:** Open your browser and navigate to `http://localhost:8080`. You can use the UI to connect, send messages, and see the echo responses.

## Deploy to Google Cloud Run

This server can be deployed directly from source to Google Cloud Run. Google Cloud's buildpacks will automatically detect the Python application, build a container image, and deploy it.

1.  **Set your Project ID:** First, set your Google Cloud Project ID as an environment variable. The following command automatically detects your currently configured gcloud project.

    ```bash
    export PROJECT_ID=$(gcloud config get-value project)
    echo "Using project: $PROJECT_ID"
    ```

2.  **Enable APIs:** Ensure you have the Cloud Build and Cloud Run APIs enabled in your Google Cloud project.

    ```bash
    gcloud services enable build.googleapis.com run.googleapis.com iam.googleapis.com --project $PROJECT_ID
    ```

3.  **Create a Service Account:** Create a dedicated service account for the Cloud Run service to follow the principle of least privilege.

    ```bash
    export SERVICE_ACCOUNT_NAME="websocket-echo-sa"
    export SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
      --display-name="WebSocket Echo Service Account" \
      --project $PROJECT_ID
    ```

4.  **Grant Permissions:** Grant the necessary roles to the service account. The `roles/monitoring.metricWriter` role allows the service to write metrics to Google Cloud Monitoring.

    ```bash
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
      --role="roles/monitoring.metricWriter"
    ```

5.  **Deploy from Source:** Deploy the application directly from your local source code, specifying the service account to be used by the Cloud Run service.

    ```bash
    gcloud run deploy websocket-echo \
      --source . \
      --region us-central1 \
      --service-account=$SERVICE_ACCOUNT_EMAIL \
      --allow-unauthenticated \
      --project $PROJECT_ID
    ```
      
    Cloud Run will automatically use the `PORT` environment variable, which defaults to 8080. Once deployed, you can access the test client at the URL provided by Cloud Run.

6.  **Verify Metrics in Cloud Monitoring:** After deploying and sending some test messages, you can view the custom metrics in the Google Cloud Console.

    1.  Navigate to **Metrics Explorer** in the Cloud Monitoring section.
    2.  In the "Select a metric" configuration, choose the following:
        -   **Resource type**: `Cloud Run Revision` (`cloud_run_revision`)
        -   **Metric**: Find metrics with the prefix `custom.googleapis.com/opentelemetry/`, for example:
            -   `custom.googleapis.com/opentelemetry/websocket_connections_total`
            -   `custom.googleapis.com/opentelemetry/websocket_active_connections`
    3.  You can filter by `service_name` to see metrics for your specific `websocket-echo` service.

    > It may take a few minutes for the metrics to appear after the service starts and receives traffic.

## Cleanup

To avoid incurring charges, you can delete the resources you created.

1.  **Delete the Cloud Run service:**

    ```bash
    gcloud run services delete websocket-echo \
      --region us-central1 \
      --platform managed \
      --project $PROJECT_ID
    ```

2.  **Delete the Service Account:**

    ```bash
    gcloud iam service-accounts delete $SERVICE_ACCOUNT_EMAIL \
      --project $PROJECT_ID
    ```

## Notes and considerations
- Cloud Run scales to zero.
- For production environments, consider adding health checks, structured logging, and authentication.
