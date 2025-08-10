# Red Hat Status Checker - Professional Monitoring Platform

A comprehensive, enterprise-grade Python monitoring solution for Red Hat services, featuring a modular architecture, statistical analytics, a Prometheus exporter, and a foundation for an OpenShift Operator.

**Version:** 3.1.1 - Docker Testing Infrastructure Edition

## Table of Contents

- [🚀 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🏗️ Architecture](#️-architecture)
- [🏆 Red Hat Enterprise Integration](#-red-hat-enterprise-integration)
  - [OpenShift Operator](#openshift-operator)
  - [Prometheus Exporter](#prometheus-exporter)
- [� System Requirements](#-system-requirements)
- [�🚀 Quick Start](#-quick-start)
- [📊 Core Features](#-core-features)
- [🏭 Enterprise Features](#-enterprise-features)
  - [Statistical Analysis and Forecasting](#statistical-analysis-and-forecasting)
  - [Multi-Channel Notifications](#multi-channel-notifications)
  - [Database Management](#database-management)
- [🐳 Container Deployment](#-container-deployment)
- [🧪 Testing Infrastructure](#-testing-infrastructure)
- [⚙️ Configuration](#️-configuration)
- [📋 Command Line Interface](#-command-line-interface)
- [🔧 Troubleshooting](#-troubleshooting)

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
- 🧪 **Enterprise Testing**: Comprehensive testing infrastructure with 400+ tests, automated permission management, and CI/CD ready validation.

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

## � System Requirements

### Python Requirements
- **Python 3.8 or higher** (tested with 3.8, 3.9, 3.10, 3.11, 3.12)
- **pip package manager**

### System Dependencies
- **SQLite3**: Required for database operations and command-line database tools
  ```bash
  # Ubuntu/Debian
  sudo apt update
  sudo apt install sqlite3
  
  # RHEL/CentOS/Fedora
  sudo dnf install sqlite
  
  # macOS
  brew install sqlite3
  ```

### Python Dependencies
All Python dependencies are automatically managed through `requirements.txt`:

**Core Dependencies:**
- `requests>=2.25.0` - HTTP API client
- `urllib3>=1.26.0` - HTTP connection pooling  
- `prometheus-client>=0.14.0` - Metrics export
- `Flask>=2.0.0` - Web UI framework

**Testing Dependencies:**
- `pytest>=7.0.0` - Test framework
- `numpy>=1.20.0` - Statistical analysis
- `pytest-cov>=4.0.0` - Test coverage

**Note**: All built-in Python modules (`sqlite3`, `json`, `logging`, etc.) are included with Python 3.8+.

---

## �🚀 Quick Start

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

The application is fully containerized for both **Docker** and **Podman** with comprehensive testing infrastructure.

### Quick Container Usage
- **Build the container**: `docker build -t redhat-status-checker .`
- **Run a quick check**: `docker run --rm redhat-status-checker quick`
- **Run with Exporter**: `docker run --rm -p 8000:8000 redhat-status-checker --enable-exporter`

### 🧪 Container Testing Infrastructure

We provide comprehensive testing suites for both Docker and Podman with enterprise-grade automation:

#### Docker Testing
```bash
# Quick unit testing
./test-docker.sh --unit-only

# Full comprehensive testing  
./test-docker.sh --comprehensive

# PyTest integration testing
python -m pytest tests/test_docker_integration.py -v

# Complete validation
./comprehensive-docker-test.sh
```

#### Podman Testing
```bash
# Podman unit testing
./test-podman.sh --unit-only

# Podman integration testing
python -m pytest tests/test_podman_integration.py -v
```

#### Permission Management
If you encounter Docker permission issues, use our automated fix:
```bash
./fix-docker-permissions.sh
./verify-docker-setup.sh  # Run after session restart
```

#### Test Coverage
- **60+ Docker tests** across integration, unit, and infrastructure validation
- **40+ Podman tests** with equivalent functionality
- **Permission-aware testing** with intelligent skip behavior
- **Professional error handling** with clear user guidance

Refer to the `Dockerfile`, `Dockerfile.test`, and `docker-compose.test.yml` for more details.

## 🧪 Testing Infrastructure

The Red Hat Status Checker includes comprehensive testing infrastructure with enterprise-grade automation and validation capabilities.

### 🏗️ Test Architecture

Our testing infrastructure provides complete coverage across multiple dimensions:

- **Unit Tests**: 358+ tests covering all core functionality
- **Integration Tests**: End-to-end workflow validation
- **Container Tests**: Docker and Podman runtime validation
- **Permission Tests**: Automated setup and validation
- **Performance Tests**: Benchmarking and optimization validation

### 🐳 Container Testing

#### Docker Testing Suite
```bash
# Quick validation (recommended for CI/CD)
./test-docker.sh --unit-only

# Comprehensive testing (full validation)
./test-docker.sh --comprehensive

# Integration testing
python -m pytest tests/test_docker_integration.py -v

# Infrastructure validation
./comprehensive-docker-test.sh
```

#### Podman Testing Suite
```bash
# Podman unit tests
./test-podman.sh --unit-only

# Podman integration tests
python -m pytest tests/test_podman_integration.py -v
```

### 🔧 Permission Management

Our automated permission management ensures smooth Docker setup:

```bash
# Automated Docker permission setup
./fix-docker-permissions.sh

# Verify setup after session restart
./verify-docker-setup.sh

# Manual validation
docker ps  # Should work without sudo
```

### 📊 Test Coverage

| Test Suite | Coverage | Status |
|------------|----------|--------|
| **Unit Tests** | 358+ tests | ✅ Comprehensive |
| **Docker Integration** | 23 tests | ✅ Full coverage |
| **Docker Containers** | 19 tests | ✅ Complete |
| **Docker Permissions** | 16 tests | ✅ Automated |
| **Podman Integration** | 22 tests | ✅ Equivalent |
| **Infrastructure** | 100+ tests | ✅ Enterprise-grade |

### 🎯 Testing Best Practices

- **Permission-Aware**: Tests intelligently skip when container runtimes unavailable
- **Error Handling**: Professional degradation with clear user guidance
- **Automation Ready**: Full CI/CD integration with proper exit codes
- **Documentation**: Comprehensive help and examples for all test scripts
- **Validation**: Complete infrastructure and functionality validation

### 🚀 Quick Testing Commands

```bash
# Validate everything is working
./comprehensive-docker-test.sh

# Run core application tests
python -m pytest tests/ -v

# Validate specific components
python -m pytest tests/test_ai_analytics.py -v      # AI features
python -m pytest tests/test_api_client.py -v        # API client
python -m pytest tests/test_database_manager.py -v  # Database
python -m pytest tests/test_web_app.py -v           # Web interface
```

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

**Advanced Analytics Flags:**
- `--ai-insights`: AI-powered health analysis and anomaly detection.
- `--health-report`: Comprehensive health report with statistics.
- `--trends`: Historical availability trends and analysis.
- `--anomaly-analysis`: Focused anomaly detection analysis.
- `--benchmark`: Performance benchmark tests for system components.

For a full list of commands, run `python3 redhat_status.py --help`.

### 🧪 Testing Commands

The project includes comprehensive testing scripts for validation and CI/CD:

| Script | Purpose |
|--------|---------|
| `./test-docker.sh --unit-only` | Quick Docker container testing |
| `./test-docker.sh --comprehensive` | Full Docker testing suite |
| `./test-podman.sh --unit-only` | Podman container testing |
| `./comprehensive-docker-test.sh` | Complete infrastructure validation |
| `./fix-docker-permissions.sh` | Automated Docker permission setup |
| `./verify-docker-setup.sh` | Post-setup verification |

**Testing Examples:**
```bash
# Validate complete infrastructure
./comprehensive-docker-test.sh

# Run specific test suites
python -m pytest tests/test_docker_integration.py -v
python -m pytest tests/test_ai_analytics.py -v

# Container testing
./test-docker.sh --help  # See all options
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Database Issues
- **Error: "no such table: service_statuses"**
  - This has been fixed in the current version
  - If you encounter this, ensure you're using the latest code

- **Error: "UNIQUE constraint failed: service_snapshots.timestamp"**
  - This occurs when running the application multiple times per second
  - Fixed with `INSERT OR REPLACE` logic in the current version

#### SQLite Issues
- **Error: "sqlite3 command not found"**
  ```bash
  # Ubuntu/Debian
  sudo apt install sqlite3
  
  # RHEL/CentOS/Fedora
  sudo dnf install sqlite
  
  # macOS
  brew install sqlite3
  ```

#### Email Notification Warnings
- **Warning: "Email configuration invalid"**
  - This is expected with default configuration
  - Configure valid SMTP settings in `config.json` to enable email notifications
  - The warning has been reduced to INFO level and won't appear during normal operation

#### AI Analytics Issues
- **Error: "Insufficient data for predictions"**
  - This is normal when the application is first run
  - Run `quick` or `simple` mode several times to collect baseline data
  - Historical data is required for trend analysis and anomaly detection

#### Performance Issues
- **Slow database operations**
  - Ensure SQLite database file isn't on a network filesystem
  - Check disk space and I/O performance
  - Database is automatically optimized with indexes

### Getting Help
- Check the logs in `redhat_status.log`
- Run with `--benchmark` to test system performance
- Use `--health-report` to check overall system status
- Review configuration in `config.json` for customization options

---
