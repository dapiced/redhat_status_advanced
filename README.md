# Red Hat Status Checker - Professional Monitoring Platform

A comprehensive, enterprise-grade Python monitoring solution for Red Hat services, featuring a modular architecture, statistical analytics, a Prometheus exporter, and a foundation for an OpenShift Operator.

**Version:** 4.0.0 - Cloud-Native Edition

## Table of Contents

- [🚀 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🏗️ Architecture](#️-architecture)
- [🏆 Red Hat Enterprise Integration](#-red-hat-enterprise-integration)
  - [OpenShift Operator](#openshift-operator)
  - [Prometheus Exporter](#prometheus-exporter)
- [🚀 Quick Start](#-quick-start)
- [📊 Core Features](#-core-features)
- [🏭 Enterprise Features](#-enterprise-features)
  - [Statistical Analysis and Forecasting](#statistical-analysis-and-forecasting)
  - [Multi-Channel Notifications](#multi-channel-notifications)
  - [Database Management](#database-management)
- [🐳 Container Deployment](#-container-deployment)
- [⚙️ Configuration](#️-configuration)
- [📋 Command Line Interface](#-command-line-interface)

---

## 🚀 Overview

The Red Hat Status Checker is a sophisticated monitoring platform that provides real-time and historical visibility into Red Hat's service health. Built with a modular, cloud-native architecture, it is designed for enterprise scalability, maintainability, and seamless integration with modern DevOps and SRE workflows.

This tool goes beyond simple status checking by storing historical data, performing statistical analysis to detect anomalies and forecast trends, and exposing this data through a CLI, a web UI, and a Prometheus exporter.

## ✨ Key Features

- 🏗️ **Modular Architecture**: Professional, maintainable codebase with clear separation of concerns.
- ☸️ **Cloud-Native Ready**: Includes a **Prometheus exporter** for easy integration with OpenShift Monitoring and a foundation for a full **OpenShift Operator**.
- 📈 **Statistical Analysis & Forecasting**:
  - **Anomaly Detection**: Uses Z-score statistical analysis to identify significant deviations from performance baselines.
  - **Trend Forecasting**: Employs linear regression to predict future service health trends.
- 📊 **Multiple Interfaces**: Access data via a comprehensive **CLI**, a simple **Web UI**, or a **Prometheus Exporter**.
- 💾 **Data Persistence**: Stores historical status data in a local SQLite database for trend analysis.
- 🔔 **Multi-Channel Alerting**: Delivers notifications through email and webhooks (Slack, Teams, etc.).
- 🐳 **Container-First**: Full support for Docker and Podman, with detailed examples for local and orchestrated environments.

## 🏗️ Architecture

The application is designed with a clean separation of concerns, making it easy to maintain and extend.

```mermaid
graph TD
    subgraph "User Interfaces"
        CLI[💻 Command Line Interface]
        WebUI[🌐 Web UI]
        Exporter[📈 Prometheus Exporter]
    end

    subgraph "Application Core"
        Main[main.py]
        Config[Config Manager]
        APIClient[API Client]
        Presenter[Presenter]
    end

    subgraph "Enterprise Modules"
        direction LR
        Analytics[🤖 Statistical Analytics]
        Database[💾 Database Manager]
        Notifications[🔔 Notification Manager]
    end

    subgraph "External Systems"
        direction LR
        RedHatAPI[Red Hat Status API]
        Prometheus[Prometheus Server]
        SMTP[Email/Webhook Services]
    end

    CLI --> Main
    WebUI --> Main
    Exporter --> Main
    Main --> Config
    Main --> APIClient
    Main --> Presenter
    Main --> Analytics
    Main --> Database
    Main --> Notifications
    
    APIClient --> RedHatAPI
    APIClient --> Database
    Analytics --> Database
    Notifications --> SMTP
    Exporter --> Prometheus
```

## 🏆 Red Hat Enterprise Integration

This tool is designed to provide maximum value within the Red Hat ecosystem.

### OpenShift Operator

The repository includes the foundational structure for a **Kubernetes Operator** in the `/operator` directory. An Operator automates the deployment, scaling, and management of the status checker on OpenShift and other Kubernetes platforms.

- **Deploy with Ease**: Use a simple Custom Resource (CR) to deploy the application.
- **Automated Management**: The Operator pattern allows for automated updates, backups, and lifecycle management.
- **OpenShift Native**: Built to feel like a native part of the OpenShift platform.

See the `operator/` directory for the CRD and example Custom Resource.

### Prometheus Exporter

The built-in Prometheus exporter allows for seamless integration with **OpenShift Monitoring**, which is built on Prometheus.

- **Run the exporter**: `python3 redhat_status.py --enable-exporter`
- **Scrape Metrics**: Configure the OpenShift monitoring stack to scrape the `/metrics` endpoint on port 8000.
- **Build Dashboards**: Use the exported metrics to build Grafana dashboards and configure Alertmanager rules directly within the OpenShift console.

---

## 🚀 Quick Start

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd redhat-status-checker
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run a quick check**:
    ```bash
    python3 redhat_status.py quick
    ```

4.  **Run the Prometheus Exporter**:
    ```bash
    python3 redhat_status.py --enable-exporter
    ```

5.  **Run the Web UI**:
    ```bash
    python3 redhat_status.py --web
    ```

## 📊 Core Features

- **Global Status Monitoring**: Real-time status with overall availability percentage.
- **Service Hierarchy Analysis**: View status for main services and their sub-components.
- **Performance Metrics**: Track API response times and cache efficiency.
- **Data Export**: Export raw data to JSON or summary reports to text files.

## 🏭 Enterprise Features

### Statistical Analysis and Forecasting

This tool uses historical data to provide intelligent insights without the overhead of a full machine learning framework.

-   **Anomaly Detection**: By calculating a historical baseline for each service, the tool can identify statistically significant deviations from normal behavior using a **Z-score**. This helps detect subtle performance degradations before they become major issues.
-   **Trend Forecasting**: Using **simple linear regression**, the tool can forecast future availability and performance trends, helping teams to proactively address potential problems.

```bash
# Get a summary of the latest analytics
python3 redhat_status.py --analytics-summary

# View current availability trends
python3 redhat_status.py --trends
```

### Multi-Channel Notifications

- **Email Alerts**: SMTP-based notifications with HTML templates.
- **Webhook Integration**: Send alerts to Slack, Microsoft Teams, Discord, and other compatible services.
- **Configurable Rules**: Control when and how notifications are sent.

### Database Management

- **SQLite Storage**: A self-contained SQLite database stores historical metrics for analysis.
- **Data Retention**: Configuration options for automatic data cleanup and retention policies.
- **Performance Optimized**: The database is indexed and can be manually maintained for optimal performance.

## 🐳 Container Deployment

The application is fully containerized for both **Docker** and **Podman**.

- **Build the container**: `docker build -t redhat-status-checker .`
- **Run a quick check**: `docker run --rm redhat-status-checker quick`
- **Run with Exporter**: `docker run --rm -p 8000:8000 redhat-status-checker --enable-exporter`

Refer to the `Dockerfile` and `docker-compose.test.yml` for more details.

## ⚙️ Configuration

Application behavior is controlled by `config.json`. Key sections include:
- `api`: Red Hat Status API endpoint and retry settings.
- `cache`: Caching TTL, size, and compression.
- `database`: Database path and data retention settings.
- `ai_analytics`: Configuration for anomaly detection and forecasting sensitivity.
- `notifications`: SMTP and webhook settings.

## 📋 Command Line Interface

The application provides a rich CLI for scripting and automation.

| Mode | Description |
|---|---|
| `quick` | Global status with availability percentage. |
| `simple`| Main services monitoring. |
| `full`  | Complete service hierarchy. |
| `export`| Export data to files. |

**Common Flags:**
- `--watch <seconds>`: Run in live monitoring mode.
- `--filter <status>`: Filter services by status (`issues`, `operational`, etc.).
- `--search <term>`: Search for a specific service by name.
- `--performance`: Show performance metrics after a run.
- `--enable-exporter`: Run the Prometheus exporter.
- `--web`: Run the Flask web UI.

For a full list of commands, run `python3 redhat_status.py --help`.
