# Red Hat Status Checker - Advanced

A comprehensive Python monitoring solution for Red Hat services with analytics, notifications, and Prometheus integration.

**Version:** 3.1.1 - Production Edition

## 🚀 Overview

Red Hat Status Checker is an enterprise-grade monitoring tool that tracks Red Hat service health in real-time. It provides statistical analysis, historical data storage, and integrates with Prometheus for comprehensive monitoring workflows.

## ✨ Features

- **Real-time Monitoring**: Track Red Hat service health and availability
- **Statistical Analysis**: Anomaly detection and trend forecasting using Z-score analysis
- **Prometheus Integration**: Built-in exporter for metrics collection
- **Multi-Channel Alerts**: Email and webhook notifications (Slack, Teams, etc.)
- **Historical Data**: SQLite database for trend analysis and reporting
- **CLI Interface**: Comprehensive command-line tools for automation
- **Modular Architecture**: Clean, maintainable codebase

## 📋 Requirements

### System Requirements
- **Python 3.8+** (compatible with 3.8-3.12)
- **SQLite3** for database operations

### Python Dependencies
Install via `requirements.txt`:
- `requests>=2.25.0` - HTTP client
- `urllib3>=1.26.0` - Connection pooling  
- `prometheus-client>=0.14.0` - Metrics export
- `numpy>=1.20.0` - Statistical analysis

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run a quick status check**:
   ```bash
   python3 redhat_status.py quick
   ```

3. **Start Prometheus exporter**:
   ```bash
   python3 redhat_status.py --enable-exporter
   ```

4. **View help for all options**:
   ```bash
   python3 redhat_status.py --help
   ```

## 📊 Usage

### Basic Commands

| Command | Description |
|---------|-------------|
| `python3 redhat_status.py quick` | Global status with availability percentage |
| `python3 redhat_status.py simple` | Main services monitoring |
| `python3 redhat_status.py full` | Complete service hierarchy |
| `python3 redhat_status.py export` | Export data to files |

### Advanced Options

| Flag | Description |
|------|-------------|
| `--watch <seconds>` | Live monitoring mode |
| `--filter <status>` | Filter by status (issues, operational, etc.) |
| `--search <term>` | Search for specific service |
| `--performance` | Show performance metrics |
| `--ai-insights` | AI-powered health analysis |
| `--trends` | Historical availability trends |
| `--enable-exporter` | Start Prometheus exporter on port 8000 |

### Analytics Features

- **Anomaly Detection**: Uses Z-score analysis to identify service issues
- **Trend Forecasting**: Linear regression for predicting future availability
- **Health Reports**: Comprehensive statistics and insights

```bash
# Get analytics summary
python3 redhat_status.py --analytics-summary

# View trends and anomalies
python3 redhat_status.py --trends --anomaly-analysis
```

## ⚙️ Configuration

The application uses `config.json` for configuration. Key sections:

- **api**: Red Hat Status API settings and retry configuration
- **cache**: Caching TTL, size, and compression options  
- **database**: Database path and data retention policies
- **ai_analytics**: Anomaly detection and forecasting sensitivity
- **notifications**: SMTP and webhook settings for alerts

Example configuration structure:
```json

  "api": {
    "base_url": "https://status.redhat.com/api/v2/summary.json",
    "timeout": 10,
    "max_retries": 3
  },
  "cache": {
    "enabled": true,
    "duration_minutes": 5,
    "directory": ".cache",
    "max_size_mb": 100,
    "auto_cleanup": true
  },
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
  "slo": {
    "enabled": true,
    "targets": {
      "global_availability": 99.9,
      "response_time": 2.0,
      "uptime_monthly": 99.5
    },
    "tracking_period": "monthly",
    "alert_on_breach": true
  },
  "notifications": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "use_tls": true,
      "from_address": "test@example.com",
      "to_addresses": [
        "admin@example.com",
        "ops@example.com"
      ],
      "username": "test@example.com",
      "password": "test-password"
    },
    "webhooks": {
      "enabled": true,
      "urls": [
        "https://hooks.slack.com/services/TEST/WEBHOOK/URL"
      ]
    },
    "slack": {
      "enabled": false
    }
  },
  "logging": {
    "enabled": true,
    "level": "INFO",
    "file": "redhat_status.log",
    "max_size_mb": 10,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  "output": {
    "default_directory": ".",
    "create_summary_report": true,
    "timestamp_format": "%Y%m%d_%H%M%S",
    "max_file_size_mb": 50,
    "compression": false
  },
  "performance": {
    "enable_metrics": true,
    "detailed_timing": false,
    "memory_profiling": false,
    "max_concurrent_operations": 5
  }
}
```

## 🔧 Troubleshooting

### Common Issues

**Database Errors**
- Ensure SQLite3 is installed: `sudo apt install sqlite3` (Ubuntu) or `sudo dnf install sqlite` (RHEL/Fedora)
- Database issues are automatically handled in the current version

**Email Notifications**  
- Configure valid SMTP settings in `config.json` to enable email alerts
- Default configuration shows warnings which can be ignored

**Analytics Issues**
- "Insufficient data" is normal on first run - collect data by running commands multiple times
- Historical data is required for trend analysis and anomaly detection

**Performance Issues**
- Use `--benchmark` to test system performance
- Check disk space and ensure database isn't on network filesystem
- Database is automatically optimized with indexes

### Getting Help
- Check logs in `redhat_status.log`
- Run `--health-report` for system status overview
- Use `--help` for complete command reference
