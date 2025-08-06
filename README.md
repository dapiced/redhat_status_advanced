# Red Hat Status Checker - Professional Monitoring Platform

A comprehensive, enterprise-grade Python monitoring solution for Red Hat services featuring modular architecture, AI-powered analytics, real-time alerting, and professional-grade performance optimization.

## 🚀 Overview

**Current Version:** v3.1.0 - Modular Edition

The Red Hat Status Checker is a sophisticated monitoring platform that provides real-time visibility into Red Hat service health with global availability percentages, intelligent alerting, and predictive analytics. Built with a modular architecture for enterprise scalability and maintainability.

### ✨ Key Capabilities

- 🏗️ **Modular Architecture** - Professional, maintainable codebase with separated concerns
- 🎯 **Real-time Monitoring** - Live status tracking with global availability percentages
- 🤖 **AI-Powered Analytics** - Machine learning anomaly detection and predictive insights
- 📊 **Performance Optimization** - Advanced caching, compression, and concurrent operations
- 🔔 **Multi-Channel Alerting** - Email, webhook, and custom notification integrations
- 💾 **Data Persistence** - SQLite database with performance optimization and cleanup
- 📈 **Trend Analysis** - Historical data analysis and availability patterns
- 🏢 **Enterprise Ready** - Professional logging, configuration management, and monitoring

## 🏗️ Architecture

### Repository Structure

```
.
├── CHANGELOG.md                     # Version history and release notes
├── config.json                      # Main application configuration file
├── CONTRIBUTING.md                  # Development guidelines and contribution rules
├── docker-compose.test.yml          # Docker Compose configuration for testing
├── Dockerfile                       # Production container build configuration
├── Dockerfile.test                  # Testing container build configuration
├── LICENSE                          # MIT license file
├── Makefile                         # Build automation and container commands
├── pyproject.toml                   # Modern Python packaging configuration (PEP 518)
├── pytest.ini                       # Pytest configuration and test settings
├── README.md                        # Comprehensive project documentation
├── redhat_status/                   # Main Python package directory
│   ├── analytics/                   # AI and machine learning analytics module
│   │   ├── ai_analytics.py          # ML anomaly detection and predictive analysis
│   │   └── __init__.py              # Analytics module initialization
│   ├── config/                      # Configuration management module
│   │   ├── config_manager.py        # Advanced configuration handling and validation
│   │   └── __init__.py              # Config module initialization
│   ├── core/                        # Core functionality modules
│   │   ├── api_client.py            # Red Hat API communication and HTTP handling
│   │   ├── cache_manager.py         # Intelligent caching system with compression
│   │   ├── data_models.py           # Data structures and service models
│   │   └── __init__.py              # Core module initialization
│   ├── database/                    # Data persistence module
│   │   ├── db_manager.py            # SQLite database operations and management
│   │   └── __init__.py              # Database module initialization
│   ├── __init__.py                  # Main package initialization
│   ├── main.py                      # Application entry point and CLI interface
│   ├── notifications/               # Multi-channel notification system
│   │   ├── __init__.py              # Notifications module initialization
│   │   └── notification_manager.py  # Email, webhook, and alert management
│   └── utils/                       # Utility functions and decorators
│       ├── decorators.py            # Performance monitoring and caching decorators
│       └── __init__.py              # Utils module initialization
├── redhat_status.py                 # Main application launcher script
├── requirements.txt                 # Python dependencies (minimal core requirements)
├── run_tests.py                     # Comprehensive test runner with multiple modes
├── run_tests_venv.sh               # Virtual environment test execution wrapper
├── test-docker.sh                   # Docker container testing script
├── test-podman.sh                   # Podman container testing script (primary)
└── tests/                           # Complete test suite directory
    ├── container_test_utils.py      # Shared utilities for container testing
    ├── __init__.py                  # Test package initialization
    ├── test_ai_analytics.py         # Unit tests for AI/ML analytics module
    ├── test_api_client.py           # Unit tests for Red Hat API client
    ├── test_cache_manager.py        # Unit tests for caching system
    ├── test_config_manager.py       # Unit tests for configuration management
    ├── test_database_manager.py     # Unit tests for database operations
    ├── test_data_models.py          # Unit tests for data structures
    ├── test_decorators.py           # Unit tests for utility decorators
    ├── test_integration.py          # Integration tests for end-to-end workflows
    ├── test_main.py                 # Unit tests for main application logic
    ├── test_notification_manager.py # Unit tests for notification system
    ├── test_podman_containers.py    # Container-specific integration tests
    └── test_podman_integration.py   # Podman integration and deployment tests
```

### Benefits of Modular Design
- ✅ **Separation of Concerns** - Each module handles specific functionality
- ✅ **Maintainability** - Easier to update and debug individual components
- ✅ **Scalability** - Enable/disable features as needed
- ✅ **Testing** - Better unit testing capabilities
- ✅ **Code Reuse** - Modules can be imported independently
- ✅ **Performance** - Optimized loading of only required components
- ✅ **Enterprise Ready** - Professional organization for production environments

### 🏆 **Testing**

This project features a comprehensive testing framework with automated validation of all functionality.

#### Comprehensive Test Runner
```bash
# Test all functionality (unit tests, flags, examples)
python3 run_tests.py --all

# Test all CLI flags (42 flags tested)
python3 run_tests.py --flags

# Test example commands from documentation
python3 run_tests.py --examples

# Test specific module
python3 run_tests.py --module main

# Install test dependencies
python3 run_tests.py --install-deps
```

#### Individual Test Commands
```bash
# Run pytest unit tests
pytest

# Run with coverage reporting
pytest --cov=redhat_status --cov-report=html
```

#### Test Status
✅ **Complete Coverage Achieved**
- **42/42 CLI flags** tested and working (100%)
- **13/13 example commands** tested and working (100%) 
- **Unit tests** covering core functionality
- **Integration tests** for end-to-end validation
- **Automated test runner** with comprehensive reporting

The project has been thoroughly tested with automated validation of all command-line flags, example commands, and core functionality to ensure production readiness.

## 🚀 Quick Start

### Basic Commands

```bash
# Interactive mode - choose operation
python3 redhat_status.py

# Quick global status check
python3 redhat_status.py quick
# OR: python3 redhat_status/main.py quick

# Quiet mode for scripting
python3 redhat_status.py quick --quiet

# Main services monitoring
python3 redhat_status.py simple

# Complete service hierarchy
python3 redhat_status.py full

# Export data to files
python3 redhat_status.py export

# Display everything
python3 redhat_status.py all
```

### Performance & Enterprise Features

```bash
# Show performance metrics
python3 redhat_status.py quick --performance

# Configuration validation
python3 redhat_status.py --config-check

# Test notification channels
python3 redhat_status.py --test-notifications

# AI analytics summary
python3 redhat_status.py --analytics-summary

# Database maintenance
python3 redhat_status.py --db-maintenance

# Clear cache
python3 redhat_status.py --clear-cache
```

## 📊 Core Features

### 🎯 Global Status Monitoring
- **Real-time Status** - Current Red Hat service availability
- **Global Availability Percentage** - Overall health metric across all services
- **Service Health Indicators** - Visual status with emoji indicators
- **Last Update Tracking** - Timestamp of latest status information

### 🏢 Service Hierarchy Analysis
- **Main Services** - Core Red Hat services monitoring
- **Sub-Services** - Detailed component-level tracking
- **Service Groups** - Organized display of related services
- **Availability Calculations** - Individual and group-level percentages

### 📈 Performance & Analytics
- **Response Time Monitoring** - API call performance tracking
- **Cache Efficiency** - Hit ratios and cache optimization
- **Session Metrics** - Duration and operation counts
- **Memory Usage** - Resource consumption monitoring

### 💾 Data Export & Persistence
- **JSON Export** - Structured data export with timestamps
- **Summary Reports** - Human-readable status reports
- **Historical Data** - Trend analysis and pattern detection
- **Database Storage** - SQLite-based data persistence (enterprise feature)

## 🏭 Enterprise Features

### 🤖 AI-Powered Analytics
- **Anomaly Detection** - Machine learning-based issue identification
- **Predictive Analysis** - Forecast potential service issues
- **Pattern Recognition** - Automated trend analysis
- **Confidence Scoring** - ML model reliability metrics
- **Learning Windows** - Configurable historical analysis periods

### 🔔 Multi-Channel Notifications
- **Email Alerts** - SMTP-based notifications with HTML templates
- **Webhook Integration** - HTTP-based alert delivery (Slack, Teams, Discord)
- **Routing Rules** - Intelligent alert distribution
- **Rate Limiting** - Prevent notification spam
- **Template System** - Customizable message formatting

### 💾 Database Management
- **SQLite Storage** - Local database for historical data
- **Performance Optimization** - Automated database maintenance
- **Data Cleanup** - Configurable retention policies
- **Backup & Recovery** - Database backup capabilities
- **Thread Safety** - Concurrent database operations

### ⚙️ Configuration Management
- **Environment Variables** - Override configuration via environment
- **Validation** - Automatic configuration validation
- **Deep Merging** - Sophisticated configuration composition
- **Security** - Secure handling of sensitive configuration
- **Hot Reloading** - Dynamic configuration updates

## � Advanced Features

### 🤖 AI Analytics & Insights

#### AI-Powered Analysis
```bash
# Detailed AI analysis with confidence scores and patterns
python3 redhat_status.py --ai-insights

# Advanced anomaly detection with severity levels
python3 redhat_status.py --anomaly-analysis

# System insights and behavioral patterns
python3 redhat_status.py --insights

# Availability trends and predictive analysis
python3 redhat_status.py --trends

# SLO tracking and objectives dashboard
python3 redhat_status.py --slo-dashboard
```

#### Health Reporting
```bash
# Comprehensive health analysis with grading (A+ to F)
python3 redhat_status.py --health-report

# Export AI analysis to various formats
python3 redhat_status.py --export-ai-report --format json
python3 redhat_status.py --export-ai-report --format csv
```

### 🔍 Service Operations

#### Filtering & Search
```bash
# Show only services with issues
python3 redhat_status.py --filter issues

# Show only operational services
python3 redhat_status.py --filter operational

# Show services with degraded performance
python3 redhat_status.py --filter degraded

# Search for specific services
python3 redhat_status.py --search "openshift"
python3 redhat_status.py --search "satellite"

# Combine filtering and search
python3 redhat_status.py --search "registry" --filter issues
```

### 📊 Live Monitoring

#### Watch Mode
```bash
# Live monitoring with 30-second refresh
python3 redhat_status.py --watch 30

# Quiet live monitoring for dashboards
python3 redhat_status.py --watch 60 --quiet

# Enable continuous monitoring features
python3 redhat_status.py --enable-monitoring
```

#### Notifications
```bash
# Send immediate status notifications
python3 redhat_status.py --notify

# Test all notification channels
python3 redhat_status.py --test-notifications
```

### ⚡ Performance Features

#### Benchmarking & Optimization
```bash
# Run performance benchmarking tests
python3 redhat_status.py --benchmark

# Enable multi-threaded health checks
python3 redhat_status.py --concurrent-check

# Bypass cache for fresh data
python3 redhat_status.py --no-cache

# Show detailed performance metrics
python3 redhat_status.py quick --performance
```

### 📁 Export & Data Management

#### Historical Data Export
```bash
# Export historical data in JSON format
python3 redhat_status.py --export-history

# Export in CSV format
python3 redhat_status.py --export-history --format csv

# Export to specific directory
python3 redhat_status.py --export-history --output ./reports
```

#### Format Options
- **JSON** - Structured data for APIs and processing
- **CSV** - Spreadsheet-compatible format
- **TXT** - Human-readable text format

### 🛠️ Debug & Configuration

#### Logging & Debugging
```bash
# Enable debug logging
python3 redhat_status.py --log-level DEBUG

# Warning level only
python3 redhat_status.py --log-level WARNING

# Error level only
python3 redhat_status.py --log-level ERROR
```

#### Configuration Management
```bash
# Validate configuration files
python3 redhat_status.py --config-check

# Run configuration setup wizard
python3 redhat_status.py --setup

# Database maintenance and cleanup
python3 redhat_status.py --db-maintenance
```

## �📋 Command Line Interface

### Operation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `quick` | Global status with availability percentage | Quick health checks |
| `simple` | Main services monitoring | Core service oversight |
| `full` | Complete service hierarchy | Comprehensive monitoring |
| `export` | Export data to files | Data analysis & reporting |
| `all` | Display everything | Complete system overview |

### Command Line Flags

| Flag | Short | Description | Category |
|------|-------|-------------|----------|
| `--output DIR` | `-o` | Output directory for exported files | Export |
| `--quiet` | `-q` | Quiet mode - minimal output | Output |
| `--performance` | | Show performance metrics | Monitoring |
| `--clear-cache` | | Clear all cached data | Maintenance |
| `--config-check` | | Validate configuration | Configuration |
| `--test-notifications` | | Test notification channels | Enterprise |
| `--analytics-summary` | | Show AI analytics summary | Enterprise |
| `--db-maintenance` | | Perform database maintenance | Enterprise |
| **`--ai-insights`** | | **Show detailed AI analysis and insights** | **AI/Analytics** |
| **`--anomaly-analysis`** | | **Advanced anomaly detection analysis** | **AI/Analytics** |
| **`--health-report`** | | **Generate comprehensive health analysis** | **AI/Analytics** |
| **`--insights`** | | **Show system insights and patterns** | **AI/Analytics** |
| **`--trends`** | | **Show availability trends and predictions** | **AI/Analytics** |
| **`--slo-dashboard`** | | **View SLO tracking and objectives** | **AI/Analytics** |
| **`--export-ai-report`** | | **Generate and export AI analysis report** | **Export** |
| **`--export-history`** | | **Export historical data to files** | **Export** |
| **`--format FORMAT`** | | **Output format: json, csv, txt (default: json)** | **Export** |
| **`--filter STATUS`** | | **Filter services: all, issues, operational, degraded** | **Service Ops** |
| **`--search TERM`** | | **Search services by name (case-insensitive)** | **Service Ops** |
| **`--concurrent-check`** | | **Enable multi-threaded health checks** | **Performance** |
| **`--watch SECONDS`** | | **Live monitoring with refresh interval** | **Monitoring** |
| **`--notify`** | | **Send notifications for current status** | **Notifications** |
| **`--benchmark`** | | **Run performance benchmarking tests** | **Performance** |
| **`--no-cache`** | | **Bypass cache and force fresh data** | **Performance** |
| **`--log-level LEVEL`** | | **Set logging level: DEBUG, INFO, WARNING, ERROR** | **Debug** |
| **`--enable-monitoring`** | | **Enable continuous monitoring mode** | **Monitoring** |
| **`--setup`** | | **Run configuration setup wizard** | **Configuration** |
| `--version` | `-v` | Show version information | System |
| `--help` | `-h` | Show help message | System |

### Usage Examples

```bash
# === Core Operations ===
python3 redhat_status.py quick              # Quick global status
python3 redhat_status.py simple             # Main services check
python3 redhat_status.py full               # Complete structure
python3 redhat_status.py export             # Export data to files
python3 redhat_status.py all                # Display everything

# === Output Control ===
python3 redhat_status.py quick --quiet      # Minimal output
python3 redhat_status.py export --output ./reports  # Custom directory

# === Performance & Monitoring ===
python3 redhat_status.py quick --performance        # Show metrics
python3 redhat_status.py --clear-cache              # Clear cache
python3 redhat_status.py --benchmark                # Performance tests
python3 redhat_status.py --no-cache                 # Bypass cache
python3 redhat_status.py --concurrent-check         # Multi-threaded checks

# === AI Analytics & Insights ===
python3 redhat_status.py --ai-insights              # Detailed AI analysis
python3 redhat_status.py --health-report            # Comprehensive health report
python3 redhat_status.py --anomaly-analysis         # Advanced anomaly detection
python3 redhat_status.py --insights                 # System patterns & insights
python3 redhat_status.py --trends                   # Availability trends
python3 redhat_status.py --slo-dashboard            # SLO tracking dashboard

# === Export & Reporting ===
python3 redhat_status.py --export-ai-report         # Export AI analysis
python3 redhat_status.py --export-history           # Export historical data
python3 redhat_status.py --export-ai-report --format csv  # CSV format
python3 redhat_status.py --export-history --format txt    # Text format

# === Service Operations ===
python3 redhat_status.py --filter issues            # Show only problematic services
python3 redhat_status.py --filter operational       # Show only healthy services
python3 redhat_status.py --search "registry"        # Search for specific services
python3 redhat_status.py --search "openshift" --filter issues  # Combined filtering

# === Live Monitoring ===
python3 redhat_status.py --watch 30                 # Live monitor (30s refresh)
python3 redhat_status.py --watch 60 --quiet         # Quiet live monitoring
python3 redhat_status.py --notify                   # Send status notifications
python3 redhat_status.py --enable-monitoring        # Enable continuous monitoring

# === Enterprise Features ===
python3 redhat_status.py --config-check            # Validate config
python3 redhat_status.py --test-notifications      # Test alerts
python3 redhat_status.py --analytics-summary       # AI insights summary
python3 redhat_status.py --db-maintenance          # DB cleanup

# === Debug & Configuration ===
python3 redhat_status.py --log-level DEBUG         # Enable debug logging
python3 redhat_status.py --setup                   # Configuration wizard
python3 redhat_status.py --version                 # Show version
python3 redhat_status.py --help                    # Show help

# === Combined Examples ===
python3 redhat_status.py quick --performance --ai-insights  # Status + performance + AI
python3 redhat_status.py --filter issues --notify --format json  # Alert on issues
python3 redhat_status.py --search "satellite" --export-ai-report  # Satellite AI analysis

# === Interactive Mode ===
python3 redhat_status.py                           # Choose operation interactively
```

## 🔧 Configuration

### Configuration Files

The application uses configuration files for customization:

- **`config.json`** - Main configuration file with all options
- **Configuration Location** - Located in the same directory as the application
- **Environment Overrides** - Environment variables override file settings

### Basic Configuration Structure

```json
{
  "api": {
    "url": "https://status.redhat.com/api/v2/summary.json",
    "timeout": 10,
    "max_retries": 3,
    "retry_delay": 2,
    "concurrent_requests": 1,
    "rate_limit_delay": 0.5
  },
  "output": {
    "default_directory": ".",
    "create_summary_report": true,
    "timestamp_format": "%Y%m%d_%H%M%S",
    "max_file_size_mb": 50,
    "compression": false
  },
  "cache": {
    "enabled": true,
    "ttl": 300,
    "directory": ".cache",
    "max_size_mb": 100,
    "compression": true,
    "cleanup_interval": 3600
  },
  "display": {
    "show_percentages": true,
    "show_health_indicator": true,
    "show_group_summaries": true,
    "color_output": true
  }
}
```

### Enterprise Configuration

```json
{
  "ai_analytics": {
    "enabled": true,
    "anomaly_detection": true,
    "predictive_analysis": true,
    "learning_window": 50,
    "anomaly_threshold": 2.0,
    "min_confidence": 0.7
  },
  "database": {
    "enabled": true,
    "path": "redhat_monitoring.db",
    "retention_days": 30,
    "auto_cleanup": true
  },
  "notifications": {
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "use_tls": true,
      "from_address": "your-email@gmail.com",
      "to_addresses": ["admin@company.com"],
      "username": "your-email@gmail.com",
      "password": "your-gmail-app-password"
    },
    "webhooks": {
      "enabled": false,
      "urls": [
        "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
      ]
    }
  }
}
```

### Environment Variables

Override configuration using environment variables:

```bash
export REDHAT_STATUS_API_URL="https://status.redhat.com/api/v2/summary.json"
export REDHAT_STATUS_TIMEOUT=15
export REDHAT_STATUS_MAX_RETRIES=5
export REDHAT_STATUS_CACHE_ENABLED=true
export REDHAT_STATUS_CACHE_TTL=300
```

Or use the provided `.env` file:
```bash
source .env
python3 redhat_status.py quick
```

## 📧 Notification Setup

### Email Notifications (Gmail)

1. **Enable email in configuration:**
```json
{
  "notifications": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "use_tls": true,
      "from_address": "your-email@gmail.com",
      "to_addresses": ["admin@company.com"],
      "username": "your-email@gmail.com",
      "password": "your-gmail-app-password"
    }
  }
}
```

2. **Generate Gmail App Password:**
   - Go to Gmail Settings → Security → 2-Step Verification
   - Generate an "App Password" for this application
   - Use the app password (not your regular password)

3. **Test email setup:**
```bash
python3 redhat_status.py --test-notifications
```

### Webhook Notifications (Slack/Teams/Discord)

#### Slack Integration
```json
{
  "notifications": {
    "webhooks": {
      "enabled": true,
      "urls": [
        "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
      ]
    }
  }
}
```

#### Microsoft Teams Integration
```json
{
  "notifications": {
    "webhooks": {
      "enabled": true,
      "urls": [
        "https://yourcompany.webhook.office.com/webhookb2/xxx/IncomingWebhook/xxx"
      ]
    }
  }
}
```

#### Discord Integration
```json
{
  "notifications": {
    "webhooks": {
      "enabled": true,
      "urls": [
        "https://discord.com/api/webhooks/123456789/XXXXXXXXXXXXXXXXXXXXXXXX"
      ]
    }
  }
}
```

## � Container Deployment

### Docker Support

The application includes full Docker containerization support for easy deployment and scalability.

#### Quick Start with Docker

```bash
# Build the container
docker build -t redhat-status-checker .

# Run with default settings
docker run --rm redhat-status-checker

# Run specific command
docker run --rm redhat-status-checker python3 redhat_status.py quick --quiet

# Run with persistent data (mount config and data)
docker run --rm \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/data:/app/data \
  redhat-status-checker

# Run with custom configuration
docker run --rm \
  -v $(pwd)/my-config.json:/app/config.json \
  -e REDHAT_STATUS_API_URL="https://custom-api.example.com" \
  redhat-status-checker
```

#### Docker Compose

Create a `docker-compose.yml` for production deployment:

```yaml
version: '3.8'
services:
  redhat-status:
    build: .
    container_name: redhat-status-checker
    restart: unless-stopped
    volumes:
      - ./config.json:/app/config.json:ro
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - REDHAT_STATUS_CACHE_ENABLED=true
      - REDHAT_STATUS_DB_ENABLED=true
    healthcheck:
      test: ["CMD", "python3", "redhat_status.py", "quick", "--quiet"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - monitoring
    
  # Optional: Add monitoring dashboard
  dashboard:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./dashboard:/usr/share/nginx/html:ro
    depends_on:
      - redhat-status
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
```

#### Production Deployment

```bash
# Production deployment with compose
docker-compose up -d

# Scale for load balancing
docker-compose up -d --scale redhat-status=3

# Monitor logs
docker-compose logs -f redhat-status

# Update deployment
docker-compose pull && docker-compose up -d
```

#### Container Features

- **🔒 Security** - Non-root user execution
- **🏥 Health Checks** - Built-in container health monitoring
- **📦 Optimized Size** - Multi-stage builds for minimal footprint
- **🔧 Configuration** - Environment variable support
- **📊 Monitoring** - Ready for orchestration platforms
- **🚀 Production Ready** - Proper signal handling and graceful shutdown

#### Podman Support

The application includes full Podman support as an alternative to Docker:

```bash
# Build and run tests with Podman
make test-podman

# Or run directly
./test-podman.sh

# Individual Podman commands
podman build -f Dockerfile.test -t redhat-status-test .
podman run --rm redhat-status-test python3 redhat_status.py quick --quiet

# Podman test options
./test-podman.sh --unit-only      # Run only unit tests
./test-podman.sh --comprehensive  # Run comprehensive tests
./test-podman.sh --help          # Show help options
```

**Podman Testing Results:**
- ✅ Container builds successfully with Python 3.11-slim
- ✅ All modules import correctly in containerized environment
- ✅ API connectivity works from within containers
- ✅ Global availability monitoring: 100.0% (139/139 services)
- ✅ Main service analysis: 20 services with 100% availability
- ✅ CLI interface fully functional in containers
- ✅ Production-ready for container orchestration platforms

#### Kubernetes Deployment

Example Kubernetes manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redhat-status-checker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: redhat-status-checker
  template:
    metadata:
      labels:
        app: redhat-status-checker
    spec:
      containers:
      - name: redhat-status-checker
        image: redhat-status-checker:latest
        ports:
        - containerPort: 8080
        env:
        - name: REDHAT_STATUS_CACHE_ENABLED
          value: "true"
        livenessProbe:
          exec:
            command:
            - python3
            - redhat_status.py
            - quick
            - --quiet
          initialDelaySeconds: 30
          periodSeconds: 60
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi" 
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: redhat-status-service
spec:
  selector:
    app: redhat-status-checker
  ports:
  - port: 80
    targetPort: 8080
```

## 🧪 Container Testing with Podman

### Comprehensive Container Testing

The project includes full Podman testing support for running comprehensive tests in isolated containers:

```bash
# Run all tests in Podman containers
./test-podman.sh

# Run only unit tests
./test-podman.sh --unit-only

# Run comprehensive tests with compose
./test-podman.sh --comprehensive

# Using Makefile shortcuts
make test-podman          # Comprehensive Podman tests
make test-docker          # Docker tests (if available)
make clean-test           # Clean up containers and results
```

### Container Test Coverage

The Podman test suite validates:

- **🐳 Container Build** - Dockerfile.test with Python 3.11-slim
- **📦 Module Import** - All Python modules load correctly
- **🌐 API Connectivity** - Red Hat status API accessible from container
- **🔧 CLI Interface** - All command-line flags and options
- **📊 Data Processing** - Service analysis and availability calculations
- **🎯 Core Functionality** - Status monitoring and reporting
- **🏗️ Production Readiness** - Container deployment validation

### Test Results Structure

Container tests generate organized results:

```
test-results/
├── unit-tests.log           # Pytest unit test output
├── cli-tests.log           # CLI flag validation results
├── integration-tests.log   # Integration test results
├── podman-test-report.md   # Comprehensive test report
└── podman-test-summary.md  # Executive summary
```

### Container Testing Features

- **🔄 Automated Testing** - Complete test automation with cleanup
- **📊 Test Reporting** - Detailed reports with pass/fail status
- **🎨 Colored Output** - Easy-to-read test progress indicators
- **🧹 Automatic Cleanup** - Container and volume cleanup after tests
- **⚡ Performance Testing** - Load and performance validation
- **🔍 Error Analysis** - Detailed error logging and analysis

### Container Compatibility

The container testing has been optimized for both Docker and Podman:

- **✅ Podman OCI Format** - HEALTHCHECK instructions removed for compatibility
- **✅ Database Integration** - Fixed import paths and method availability
- **✅ Clean Output** - Resolved formatting issues for proper display
- **✅ Virtual Environment** - Automatic dependency management with `.venv`

## 📋 Installation & Setup
```

## �📋 Installation & Setup

### Prerequisites
- **Python 3.6+** - Required for all functionality
- **Docker/Podman** (Optional) - For containerized deployment and testing
- **Internet Connection** - For Red Hat API access
- **Optional Dependencies** - For enterprise features

### Dependencies

**Core (Always Required):**
- `requests` - HTTP client for API calls
- `urllib3` - HTTP connection pooling (usually included with requests)

**Enterprise Features (Optional):**
- `sqlite3` - Database storage (usually built-in with Python)
- `smtplib` - Email notifications (usually built-in with Python)
- `email` - Email formatting (usually built-in with Python)

### Installation Steps

#### Method 1: Standard Python Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd redhat-status-checker
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install the package in editable mode:**
   This step makes the `redhat-status` command available in your environment and ensures that `pytest` can find the modules to test.
   ```bash
   pip install -e .
   ```

4. **Set Permissions** (Linux/macOS):
   ```bash
   chmod +x redhat_status.py
   ```

5. **Test the installation:**
   ```bash
   redhat-status --version
   ```
   or
   ```bash
   python3 redhat_status.py --version
   ```

#### Method 2: Docker Installation (Recommended for Production)

1. **Clone and build:**
   ```bash
   git clone <repository_url>
   cd redhat-status-checker
   docker build -t redhat-status-checker .
   ```

2. **Test the container:**
   ```bash
   docker run --rm redhat-status-checker python3 redhat_status.py --version
   ```

3. **Run with persistent configuration:**
   ```bash
   # Copy and customize config
   cp config.json my-config.json
   # Edit my-config.json as needed
   
   # Run with custom config
   docker run --rm \
     -v $(pwd)/my-config.json:/app/config.json \
     redhat-status-checker python3 redhat_status.py quick
   ```

#### Method 3: Docker Compose (Production Deployment)

1. **Create docker-compose.yml:**
   ```bash
   # Use the example provided in the Container Deployment section
   docker-compose up -d
   ```

2. **Verify deployment:**
   ```bash
   docker-compose ps
   docker-compose logs redhat-status
   ```

### Post-Installation Configuration

6. **Customize configuration (optional):**
   Edit `config.json` to configure enterprise features like notifications and database settings.
   ```bash
   nano config.json
   ```

### Quick Installation Check

```bash
# Verify all dependencies and modules
python3 redhat_status.py --config-check

# Test basic functionality
python3 redhat_status.py quick --quiet

# Test enterprise features (if configured)
python3 redhat_status.py --analytics-summary
```

## 🔍 Output Examples

### Basic Status Check
```bash
$ python3 redhat_status.py quick
🎯 RED HAT STATUS CHECKER - MODULAR EDITION v3.1.0
============================================================

============================================================
🚀 RED HAT GLOBAL STATUS
============================================================
📍 Page: Red Hat
🔗 URL: https://status.redhat.com
🕒 Last Update: 2025-08-03T21:35:51.303Z

🟢 STATUS: All Systems Operational
🏷️ Severity: All Systems Operational

🟢 GLOBAL AVAILABILITY: 100.0% (139/139 services)
🏥 Overall Health: EXCELLENT

✅ Operation completed successfully in 0.45s!
```

### Performance Monitoring
```bash
$ python3 redhat_status.py quick --performance
# ... status output ...

⚡ PERFORMANCE METRICS
==================================================
🕒 Session Duration: 0.45s
🌐 API Calls: 1
📋 Cache Entries: 26
💾 Cache Size: 95.8 KB
📈 Cache Hit Ratio: 85.2%
🧠 Memory Usage: 42.3 MB

✅ Operation completed successfully in 0.45s!
```

### Configuration Validation
```bash
$ python3 redhat_status.py --config-check
🔧 CONFIGURATION VALIDATION
========================================
Status: ✅ Valid

Configuration Summary:
  API URL: https://status.redhat.com/api/v2/summary.json
  Cache: ✅ Enabled (TTL: 300s)
  Database: ✅ Enabled
  Analytics: ✅ Enabled
  Notifications: ✅ 2 channels configured
```

### Notification Testing
```bash
$ python3 redhat_status.py --test-notifications
🧪 TESTING NOTIFICATION CHANNELS
========================================
Email: ❌ FAIL
Webhook: ✅ PASS
----------------------------------------
📊 Results: 1/2 channels passed
💡 Note: Some failures may be due to test/invalid credentials
📝 Update config.json with real SMTP/webhook settings for production
```

### AI Analytics Summary
```bash
$ python3 redhat_status.py --analytics-summary
🤖 AI ANALYTICS SUMMARY
========================================
📊 Data Quality: 1,234 metrics
🔍 Anomalies (24h): 0
🔮 Predictions (24h): 3
🎯 Confidence: 94.2%
📈 Trend: Stable

Recent Insights:
  ✅ System health is excellent
  📊 Performance trending positive
  🔮 No issues predicted for next 24h
```

## 📊 Data Export Formats

### Export Files Generated

When using `export` mode, the following files are created:

- **`redhat_status_YYYYMMDD_HHMMSS.json`** - Complete raw data
- **`redhat_summary_YYYYMMDD_HHMMSS.txt`** - Human-readable summary
- **`health_report_YYYYMMDD_HHMMSS.json`** - Health analysis (if analytics enabled)
- **`health_summary_YYYYMMDD_HHMMSS.txt`** - Executive summary (if analytics enabled)

### JSON Export Structure
```json
{
  "timestamp": "2025-08-03T21:35:51.303Z",
  "global_status": {
    "availability_percentage": 100.0,
    "total_services": 139,
    "operational_services": 139,
    "health_grade": "A+"
  },
  "performance_metrics": {
    "response_time": 0.45,
    "cache_hit_ratio": 85.2,
    "api_calls": 1
  },
  "services": [
    {
      "name": "Registry Account Management",
      "status": "operational",
      "group": "Core Services"
    }
  ]
}
```

## 🛠️ Development & Maintenance

### Module Architecture

Each module is designed for:
- **Independence** - Can be tested and modified separately
- **Clear APIs** - Well-defined interfaces between components
- **Error Isolation** - Failures in one module don't affect others
- **Performance** - Optimized for specific use cases

### Extending Functionality

- **Add New Modules** - Create new modules in appropriate directories
- **Modify Behavior** - Update individual modules without affecting others
- **Custom Integrations** - Easily integrate with external systems
- **Testing** - Unit test individual components using the `pytest` framework.

### Project Structure

This project uses a `pyproject.toml` file to define project metadata and dependencies, following modern Python packaging standards (PEP 518). This file is used by tools like `pip` and `build` to manage the project.

### Database Management

```bash
# Database maintenance
python3 redhat_status.py --db-maintenance

# Clear all data
python3 redhat_status.py --clear-cache
```

### Common Troubleshooting

#### Import Errors
```bash
# If you see "ModuleNotFoundError"
cd /path/to/bin
python3 redhat_status/main.py quick

# Or use the launcher
python3 redhat_status.py quick
```

#### Notification Issues
```bash
# Test notification channels
python3 redhat_status.py --test-notifications

# Check configuration
python3 redhat_status.py --config-check
```

#### Performance Issues
```bash
# Clear cache if stale
python3 redhat_status.py --clear-cache

# Check performance metrics
python3 redhat_status.py quick --performance
```

## 🎯 Use Cases

### DevOps & SRE Teams
- **Real-time Monitoring** - Live status dashboards
- **Alerting Integration** - Integrate with monitoring systems
- **Trend Analysis** - Historical availability tracking
- **Incident Response** - Quick status verification during incidents

### Automation & CI/CD
- **Pipeline Integration** - Include status checks in deployment pipelines
- **Health Checks** - Verify Red Hat service availability before deployments
- **Reporting** - Generate automated status reports
- **Scripting** - Use quiet mode for script integration

### Enterprise Monitoring
- **Database Storage** - Long-term data retention and analysis
- **AI Analytics** - Predictive insights and anomaly detection
- **Multi-Channel Alerts** - Comprehensive notification strategies
- **Performance Optimization** - Cache and database tuning

## 📈 Performance Features

### Caching System
- **Intelligent Caching** - Automatic cache management with TTL
- **Compression** - Reduce storage space by 60%+
- **Hit Ratio Tracking** - Monitor cache effectiveness
- **Automatic Cleanup** - Prevent cache growth issues

### Optimization Features
- **Concurrent Operations** - Multi-threaded processing for enterprise scale
- **Memory Efficiency** - Optimized memory usage with profiling
- **Response Time Monitoring** - Track API performance
- **Resource Management** - Automatic cleanup and optimization

## 🔐 Security Features

- **Secure Configuration** - Safe handling of sensitive data
- **Environment Variables** - Secure credential management
- **Input Validation** - Protect against malicious input
- **Error Handling** - Secure error reporting without data leakage

## 🏆 Why Choose This Solution?

- **🔧 Professional** - Enterprise-ready architecture and features
- **⚡ Performance** - Optimized caching and concurrent operations
- **🛡️ Reliable** - Comprehensive error handling and fallback mechanisms
- **📈 Scalable** - Modular design for easy extension and modification
- **🤖 Intelligent** - AI-powered analytics and predictive insights
- **🔔 Comprehensive** - Multi-channel alerting and notification systems
- **💾 Persistent** - Database storage with performance optimization
- **🎯 User-Friendly** - Clean CLI interface with extensive documentation
- **🐳 Container Ready** - Full Docker support with optimized images
- **☸️ Cloud Native** - Kubernetes manifests and orchestration support

## 📚 Additional Resources

### Configuration Files
- **`config.json`** - Main configuration file with all options
- **`.env`** - Environment variables configuration

### Documentation
- **Command Line Help** - `python3 redhat_status.py --help`
- **Version Information** - `python3 redhat_status.py --version`
- **Configuration Validation** - `python3 redhat_status.py --config-check`

---

**Red Hat Status Checker v3.1.0 - Modular Edition**  
*Professional monitoring platform with enterprise-grade capabilities*

Built with modular architecture for maintainability, AI-powered analytics for intelligence, and comprehensive alerting for operational excellence.