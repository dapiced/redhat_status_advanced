# Red Hat Status Checker - Advanced

A comprehensive Python monitoring solution for Red Hat services with analytics, notifications, and Prometheus integration.

**Version:** 3.1.1 - Advanced Edition

## 🚀 Overview

Red Hat Status Checker is an enterprise-grade monitoring tool that tracks Red Hat service health in real-time. It provides statistical analysis, historical data storage, and integrates with Prometheus for comprehensive monitoring workflows.

Redhat status page is based on the software https://www.atlassian.com/software/statuspage

Redhat status page API
- https://status.redhat.com/api/v2/
- https://status.redhat.com/api/v2/summary.json

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

### Command Line Options

#### **Export and Output Flags**

| Flag | Description | Example |
|------|-------------|---------|
| `--format {json,csv,txt}` | Export format for data files | `python3 redhat_status.py export --format csv` |
| `--output <directory>` | Output directory for exported files | `python3 redhat_status.py export --output ./reports` |
| `--quiet` | Minimal output mode | `python3 redhat_status.py quick --quiet` |

#### **Monitoring and Live Features**

| Flag | Description | Example |
|------|-------------|---------|
| `--watch <seconds>` | Live monitoring with refresh interval | `python3 redhat_status.py --watch 30` |
| `--enable-monitoring` | Enable enhanced monitoring mode | `python3 redhat_status.py simple --enable-monitoring` |
| `--concurrent-check` | Enable multi-threaded health checks | `python3 redhat_status.py full --concurrent-check` |

#### **Filtering and Search**

| Flag | Description | Example |
|------|-------------|---------|
| `--filter {all,issues,operational,degraded}` | Filter services by status | `python3 redhat_status.py --filter issues` |
| `--search <term>` | Search for specific services | `python3 redhat_status.py --search "registry"` |

#### **Prometheus Exporter**

| Flag | Description | Example |
|------|-------------|---------|
| `--enable-exporter` | Start Prometheus metrics server | `python3 redhat_status.py --enable-exporter` |
| `--exporter-port <port>` | Custom port for Prometheus exporter | `python3 redhat_status.py --enable-exporter --exporter-port 9090` |

**Note**: `--exporter-port` sets the port but requires `--enable-exporter` to actually start the server.

#### **Analytics and Insights**

| Flag | Description | Example |
|------|-------------|---------|
| `--ai-insights` | AI-powered health analysis | `python3 redhat_status.py --ai-insights` |
| `--anomaly-analysis` | Advanced anomaly detection | `python3 redhat_status.py --anomaly-analysis` |
| `--health-report` | Comprehensive health report | `python3 redhat_status.py --health-report` |
| `--trends` | Historical availability trends | `python3 redhat_status.py --trends` |
| `--slo-dashboard` | View SLO tracking dashboard | `python3 redhat_status.py --slo-dashboard` |

#### **Notifications and Alerts**

| Flag | Description | Example |
|------|-------------|---------|
| `--notify` | Send notifications for current status | `python3 redhat_status.py --notify` |
| `--test-notifications` | Test all notification channels | `python3 redhat_status.py --test-notifications` |

#### **System and Debug**

| Flag | Description | Example |
|------|-------------|---------|
| `--log-level {DEBUG,INFO,WARNING,ERROR}` | Set logging verbosity | `python3 redhat_status.py quick --log-level DEBUG` |
| `--performance` | Show performance metrics | `python3 redhat_status.py simple --performance` |
| `--benchmark` | Run performance benchmarking | `python3 redhat_status.py --benchmark` |
| `--no-cache` | Bypass cache for fresh data | `python3 redhat_status.py quick --no-cache` |
| `--clear-cache` | Clear all cached data | `python3 redhat_status.py --clear-cache` |
| `--config-check` | Validate configuration | `python3 redhat_status.py --config-check` |

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

## 📖 Common Usage Examples

### **Monitoring Workflows**

```bash
# Basic status check
python3 redhat_status.py quick

# Live monitoring (refresh every 30 seconds)
python3 redhat_status.py --watch 30

# Check only services with issues
python3 redhat_status.py --filter issues

# Search for specific services
python3 redhat_status.py --search "container"
```

### **Data Export and Reporting**

```bash
# Export current status to CSV
python3 redhat_status.py export --format csv --output ./reports

# Export to JSON with custom directory
python3 redhat_status.py export --format json --output /path/to/reports

# Export historical data (requires database)
python3 redhat_status.py --export-history --format csv
```

### **Prometheus Integration**

```bash
# Start exporter on default port 8000
python3 redhat_status.py --enable-exporter

# Start exporter on custom port
python3 redhat_status.py --enable-exporter --exporter-port 9090

# Run status check with exporter enabled
python3 redhat_status.py quick --enable-exporter --exporter-port 8080

# Run exporter-only mode (keeps server running)
python3 redhat_status.py --enable-exporter
# Then press Enter when prompted to run in exporter-only mode
```

**Accessing Metrics**: Once the exporter is running, metrics are available at:
- `http://localhost:8000/metrics` (default)
- `http://localhost:9090/metrics` (custom port example)

#### **Verifying Exporter Status**

**Check if the exporter port is listening:**
```bash
# Using netstat (if available)
netstat -tuln | grep 8000

# Using ss (modern alternative)
ss -tuln | grep 8000

# Expected output:
# tcp   LISTEN 0      5            0.0.0.0:8000       0.0.0.0:*
```

**Test metrics endpoint:**
```bash
# Fetch all metrics
curl -s http://localhost:8000/metrics

# Get just Red Hat specific metrics
curl -s http://localhost:8000/metrics | grep redhat

# Check specific metric (availability)
curl -s http://localhost:8000/metrics | grep "redhat_status_global_availability"
```

**Example curl output:**
```
# HELP redhat_status_global_availability_percentage Overall availability percentage of all Red Hat services
# TYPE redhat_status_global_availability_percentage gauge
redhat_status_global_availability_percentage 100.0

# HELP redhat_status_services_operational_total Total number of operational services
# TYPE redhat_status_services_operational_total gauge
redhat_status_services_operational_total 139.0

# HELP redhat_status_services_with_issues_total Total number of services with issues (non-operational)
# TYPE redhat_status_services_with_issues_total gauge
redhat_status_services_with_issues_total 0.0

# HELP redhat_status_service_status Status of an individual Red Hat service (1=operational, 0=issue)
# TYPE redhat_status_service_status gauge
redhat_status_service_status{service_name="Registry Account Management"} 1.0
redhat_status_service_status{service_name="Downloads"} 1.0
redhat_status_service_status{service_name="Catalog App"} 1.0

# HELP redhat_status_cache_hit_ratio_percentage Cache hit ratio for the API client
# TYPE redhat_status_cache_hit_ratio_percentage gauge
redhat_status_cache_hit_ratio_percentage 85.0

# HELP redhat_status_api_response_time_seconds Response time for the Red Hat Status API
# TYPE redhat_status_api_response_time_seconds gauge
redhat_status_api_response_time_seconds 0.36

# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 436.0
python_gc_objects_collected_total{generation="1"} 0.0
python_gc_objects_collected_total{generation="2"} 0.0
```

**Find what process is using a port (if conflicts occur):**
```bash
# Check what's using port 8000
lsof -i :8000

# Kill process using the port
kill $(lsof -t -i:8000)

# Or kill all exporter processes
pkill -f "redhat_status.py.*exporter"
```

**Troubleshooting Exporter Issues:**
```bash
# Check if port is already in use
ss -tuln | grep 8000

# If port is occupied, use a different port
python3 redhat_status.py --enable-exporter --exporter-port 9090

# Verify the new port is working
curl -s http://localhost:9090/metrics | head -5
```

### **Advanced Analytics**

```bash
# Comprehensive health analysis
python3 redhat_status.py --health-report

# AI-powered insights
python3 redhat_status.py --ai-insights

# Anomaly detection with trends
python3 redhat_status.py --anomaly-analysis --trends

# SLO tracking dashboard
python3 redhat_status.py --slo-dashboard
```

### **Notifications and Alerts**

```bash
# Send notifications based on current status
python3 redhat_status.py --notify

# Test notification channels
python3 redhat_status.py --test-notifications

# Run check and notify if issues found
python3 redhat_status.py quick --notify --filter issues
```

### **Debugging and Performance**

```bash
# Enable debug logging
python3 redhat_status.py quick --log-level DEBUG

# Performance monitoring with metrics
python3 redhat_status.py full --performance --concurrent-check

# Benchmark system performance
python3 redhat_status.py --benchmark

# Force fresh data (bypass cache)
python3 redhat_status.py quick --no-cache

# Validate configuration
python3 redhat_status.py --config-check
```

### **Combining Multiple Flags**

```bash
# Comprehensive monitoring setup
python3 redhat_status.py full --enable-exporter --exporter-port 9090 --log-level INFO --performance

# Export with enhanced monitoring
python3 redhat_status.py export --format csv --output ./reports --enable-monitoring --performance

# Live monitoring with notifications
python3 redhat_status.py --watch 60 --notify --filter issues --log-level WARNING
```

## ⚙️ Configuration

The application uses `config.json` for configuration. Key sections:

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

**Command Line Syntax Errors**
- **Check spelling**: Flags are case-sensitive and must match exactly
- **Use quotes** for search terms with spaces: `--search "red hat"`

**Export and Format Issues**
- **CSV Export**: The `--format csv` flag only works with `export` mode or `--export-history`
- **Output Directory**: Ensure the directory exists or use `.` for current directory
- **File Permissions**: Check write permissions in the output directory

**Prometheus Exporter Issues**
- **Port Already in Use**: Error "Address already in use" means the port is occupied
  ```bash
  # Check port availability with ss (modern)
  ss -tuln | grep 8000
  
  # Check port availability with netstat (legacy)
  netstat -tuln | grep 8000
  
  # Find what process is using the port
  lsof -i :8000
  ```
- **Solutions for Port Conflicts**:
  ```bash
  # Try a different port
  python3 redhat_status.py --enable-exporter --exporter-port 9090
  
  # Kill existing processes
  pkill -f "redhat_status.py.*exporter"
  
  # Or kill specific process by PID
  kill $(lsof -t -i:8000)
  ```
- **Exporter Not Starting**: Ensure you use `--enable-exporter`, not just `--exporter-port`
- **Metrics Not Available**: 
  ```bash
  # Test if metrics endpoint is accessible
  curl -s http://localhost:8000/metrics | head -5
  
  # Check for Red Hat specific metrics
  curl -s http://localhost:8000/metrics | grep redhat_status
  ```

**Logging and Debug Issues**
- **No Debug Output**: Use `--log-level DEBUG` to see detailed information
- **Too Much Output**: Use `--log-level ERROR` or `--quiet` to reduce verbosity
- **Log File Issues**: Check permissions for `redhat_status.log`

**Monitoring and Performance**
- **Live Monitoring Stuck**: Use `Ctrl+C` to stop `--watch` mode
- **Concurrent Check Errors**: Use `--log-level DEBUG` to see threading issues
- **Performance Issues**: Try `--benchmark` to identify bottlenecks

**Notification Problems**
- **Notifications Not Sent**: Check configuration in `config.json`
- **Webhook Errors**: Verify webhook URLs are correct and accessible
- **Email Issues**: Test SMTP settings with `--test-notifications`

### Flag-Specific Troubleshooting

| Issue | Solution |
|-------|----------|
| `--format csv` not working | Use with `export` mode: `python3 redhat_status.py export --format csv` |
| `--exporter-port` not starting server | Add `--enable-exporter`: `python3 redhat_status.py --enable-exporter --exporter-port 9090` |
| `--concurrent-check` not recognized | Use double dashes: `--concurrent-check` |
| `--log-level` shows no difference | Compare DEBUG vs ERROR levels to see the difference |
| `--enable-monitoring` seems inactive | Flag sets internal state, combine with other operations to see effect |
| `--notify` fails | Configure notification channels in `config.json` first |

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
