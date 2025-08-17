# Monitoring & Logging Guide

Complete guide to monitoring, logging, and observability for Santiq pipelines and operations.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Audit System](#audit-system)
3. [Logging Configuration](#logging-configuration)
4. [Pipeline Monitoring](#pipeline-monitoring)
5. [Performance Monitoring](#performance-monitoring)
6. [Alerting](#alerting)
7. [Troubleshooting](#troubleshooting)

## 🎯 Overview

Santiq provides comprehensive monitoring and logging capabilities to help you track pipeline execution, identify issues, and optimize performance.

### Key Features

- **Audit Trail**: Complete history of all pipeline executions
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Performance Metrics**: Execution time, memory usage, and throughput
- **Error Tracking**: Detailed error information and stack traces
- **Plugin Monitoring**: Individual plugin performance and status

## 📊 Audit System

### Audit Events

Santiq automatically logs audit events for all pipeline operations:

```python
from santiq.core.audit import AuditLogger

# Create audit logger
logger = AuditLogger("audit.log")

# Log events
logger.log_event(
    event_type="pipeline_start",
    pipeline_id="pipeline_123",
    details={"config_file": "pipeline.yml"}
)
```

### Event Types

| Event Type | Description | Details |
|------------|-------------|---------|
| `pipeline_start` | Pipeline execution started | Config file, mode, timestamp |
| `pipeline_complete` | Pipeline execution completed | Success status, rows processed |
| `pipeline_error` | Pipeline execution failed | Error message, stack trace |
| `plugin_start` | Plugin execution started | Plugin name, parameters |
| `plugin_complete` | Plugin execution completed | Success status, output size |
| `plugin_error` | Plugin execution failed | Error message, plugin context |
| `data_quality_issue` | Data quality issue detected | Issue type, severity, affected rows |
| `fix_applied` | Data quality fix applied | Fix type, affected rows |

### Audit Log Format

Audit logs are stored in JSON Lines (JSONL) format:

```json
{"timestamp": "2024-01-15T10:30:15.123Z", "event_type": "pipeline_start", "pipeline_id": "pipeline_123", "status": "success", "details": {"config_file": "pipeline.yml", "mode": "manual"}}
{"timestamp": "2024-01-15T10:30:16.456Z", "event_type": "plugin_start", "pipeline_id": "pipeline_123", "plugin_name": "csv_extractor", "status": "success", "details": {"params": {"path": "data.csv"}}}
{"timestamp": "2024-01-15T10:30:17.789Z", "event_type": "plugin_complete", "pipeline_id": "pipeline_123", "plugin_name": "csv_extractor", "status": "success", "details": {"rows_processed": 1000}}
```

### Querying Audit Logs

```bash
# View recent audit events
santiq run history

# View specific pipeline history
santiq run history --pipeline-id pipeline_123

# View more history entries
santiq run history --limit 50
```

### Programmatic Access

```python
from santiq.core.audit import AuditLogger

logger = AuditLogger("audit.log")

# Get recent events
events = logger.get_recent_events(limit=100)

# Get pipeline-specific events
pipeline_events = logger.get_pipeline_events("pipeline_123", limit=50)

# Filter events by type
pipeline_starts = [e for e in events if e.event_type == "pipeline_start"]
```

## 📝 Logging Configuration

### Log Levels

Santiq supports standard Python logging levels:

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about pipeline execution
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may require immediate attention

### Configuration

Set log level via environment variable or configuration:

```bash
# Environment variable
export SANTIQ_LOG_LEVEL=INFO

# Or in pipeline configuration
log_level: "INFO"
```

### Log Format

Logs include structured information:

```
2024-01-15 10:30:15,123 - santiq.core.engine - INFO - Starting pipeline: pipeline.yml
2024-01-15 10:30:15,456 - santiq.plugins.extractors.csv_extractor - INFO - Extracting data from: data.csv
2024-01-15 10:30:16,789 - santiq.core.pipeline - INFO - Pipeline completed successfully
```

### Log Rotation

Configure log rotation to manage disk space:

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure rotating file handler
handler = RotatingFileHandler(
    'santiq.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

# Set formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
```

## 🔍 Pipeline Monitoring

### Execution Metrics

Track key pipeline metrics:

```python
# Pipeline execution results
result = {
    'success': True,
    'pipeline_id': 'pipeline_123',
    'execution_time': 45.2,  # seconds
    'rows_processed': 10000,
    'memory_usage_mb': 512,
    'plugins_executed': 4,
    'data_quality_issues': 15,
    'fixes_applied': 12
}
```

### Real-time Monitoring

Monitor pipeline execution in real-time:

```bash
# Run with verbose output
santiq run pipeline config.yml --verbose

# Monitor log files
tail -f ~/santiq/logs/santiq.log

# Monitor audit logs
tail -f ~/santiq/logs/audit.log
```

### Pipeline Health Checks

```python
from santiq.core.engine import ETLEngine

engine = ETLEngine()

# Check pipeline health
def check_pipeline_health(pipeline_id: str) -> dict:
    events = engine.get_pipeline_history(pipeline_id, limit=10)
    
    # Analyze recent events
    recent_events = [e for e in events if e.timestamp > datetime.now() - timedelta(hours=1)]
    error_events = [e for e in recent_events if e.status == "error"]
    
    return {
        'pipeline_id': pipeline_id,
        'status': 'healthy' if len(error_events) == 0 else 'unhealthy',
        'error_count': len(error_events),
        'last_execution': recent_events[-1].timestamp if recent_events else None
    }
```

## 📈 Performance Monitoring

### Memory Usage

Monitor memory consumption:

```python
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
        'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
        'percent': process.memory_percent()
    }
```

### Execution Time

Track execution time for different pipeline stages:

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(stage_name: str):
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        print(f"{stage_name} completed in {execution_time:.2f} seconds")
```

### Throughput Metrics

Calculate data processing throughput:

```python
def calculate_throughput(rows_processed: int, execution_time: float) -> dict:
    return {
        'rows_per_second': rows_processed / execution_time,
        'megabytes_per_second': (rows_processed * 1024) / execution_time / 1024 / 1024,
        'total_rows': rows_processed,
        'execution_time': execution_time
    }
```

### Plugin Performance

Monitor individual plugin performance:

```python
def monitor_plugin_performance(plugin_name: str, execution_time: float, data_size: int):
    metrics = {
        'plugin_name': plugin_name,
        'execution_time': execution_time,
        'data_size_mb': data_size / 1024 / 1024,
        'throughput_mbps': (data_size / 1024 / 1024) / execution_time
    }
    
    # Log metrics
    logger.info(f"Plugin performance: {metrics}")
    return metrics
```

## 🚨 Alerting

### Error Alerts

Set up alerts for pipeline failures:

```python
def send_error_alert(error_event):
    alert_message = {
        'severity': 'error',
        'pipeline_id': error_event.pipeline_id,
        'error_message': error_event.details.get('error'),
        'timestamp': error_event.timestamp,
        'plugin_name': error_event.plugin_name
    }
    
    # Send alert via email, Slack, etc.
    send_alert(alert_message)
```

### Performance Alerts

Alert on performance degradation:

```python
def check_performance_thresholds(execution_time: float, memory_usage: float):
    alerts = []
    
    if execution_time > 300:  # 5 minutes
        alerts.append({
            'type': 'performance',
            'message': f'Pipeline execution time ({execution_time}s) exceeded threshold',
            'severity': 'warning'
        })
    
    if memory_usage > 4000:  # 4GB
        alerts.append({
            'type': 'performance',
            'message': f'Memory usage ({memory_usage}MB) exceeded threshold',
            'severity': 'warning'
        })
    
    return alerts
```

### Data Quality Alerts

Alert on data quality issues:

```python
def check_data_quality_alerts(issues: list):
    critical_issues = [i for i in issues if i['severity'] == 'critical']
    
    if len(critical_issues) > 0:
        return {
            'type': 'data_quality',
            'message': f'Found {len(critical_issues)} critical data quality issues',
            'severity': 'error',
            'issues': critical_issues
        }
    
    return None
```

### Integration with Monitoring Systems

#### Prometheus Integration

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
pipeline_executions = Counter('santiq_pipeline_executions_total', 'Total pipeline executions')
pipeline_duration = Histogram('santiq_pipeline_duration_seconds', 'Pipeline execution duration')
memory_usage = Gauge('santiq_memory_usage_bytes', 'Memory usage in bytes')

# Record metrics
def record_pipeline_metrics(result):
    pipeline_executions.inc()
    pipeline_duration.observe(result['execution_time'])
    memory_usage.set(result['memory_usage_mb'] * 1024 * 1024)
```

#### Grafana Dashboard

Create Grafana dashboard configuration:

```json
{
  "dashboard": {
    "title": "Santiq Pipeline Monitoring",
    "panels": [
      {
        "title": "Pipeline Executions",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(santiq_pipeline_executions_total[5m])",
            "legendFormat": "Executions/sec"
          }
        ]
      },
      {
        "title": "Pipeline Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(santiq_pipeline_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "santiq_memory_usage_bytes",
            "legendFormat": "Memory (bytes)"
          }
        ]
      }
    ]
  }
}
```

## 🔧 Troubleshooting

### Common Issues

#### High Memory Usage

```bash
# Check memory usage
ps aux | grep santiq

# Monitor memory over time
watch -n 1 'ps aux | grep santiq'

# Check for memory leaks
python -m memory_profiler your_script.py
```

#### Slow Pipeline Execution

```bash
# Profile execution time
python -m cProfile -o profile.stats your_script.py

# Analyze profile results
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

#### Plugin Failures

```bash
# Check plugin logs
tail -f ~/santiq/logs/plugin_errors.log

# Test plugin individually
santiq plugin info plugin_name

# Check plugin configuration
santiq run pipeline config.yml --dry-run
```

### Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment variables
export SANTIQ_LOG_LEVEL=DEBUG
export SANTIQ_DEBUG=true

# Run with debug output
santiq run pipeline config.yml --verbose --debug
```

### Log Analysis

Analyze logs for patterns:

```bash
# Find error patterns
grep -i error ~/santiq/logs/*.log | head -20

# Count error types
grep -i error ~/santiq/logs/*.log | cut -d' ' -f4 | sort | uniq -c

# Find slow operations
grep "completed in" ~/santiq/logs/*.log | sort -k5 -n | tail -10
```

### Performance Optimization

#### Memory Optimization

```python
# Use chunked processing for large datasets
def process_in_chunks(data, chunk_size=10000):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        yield process_chunk(chunk)

# Clear memory after processing
import gc
gc.collect()
```

#### Execution Optimization

```python
# Enable parallel processing
config = {
    'parallel_execution': True,
    'max_workers': 4
}

# Use efficient data types
import pandas as pd
df = df.astype({
    'category_column': 'category',
    'numeric_column': 'int32'
})
```

## 📊 Monitoring Dashboard

### Web-based Dashboard

Create a simple web dashboard for monitoring:

```python
from flask import Flask, render_template
from santiq.core.audit import AuditLogger

app = Flask(__name__)

@app.route('/dashboard')
def dashboard():
    logger = AuditLogger("audit.log")
    
    # Get recent events
    recent_events = logger.get_recent_events(limit=100)
    
    # Calculate metrics
    metrics = {
        'total_pipelines': len(set(e.pipeline_id for e in recent_events)),
        'success_rate': len([e for e in recent_events if e.status == 'success']) / len(recent_events),
        'avg_execution_time': calculate_avg_execution_time(recent_events)
    }
    
    return render_template('dashboard.html', metrics=metrics, events=recent_events)
```

### Real-time Updates

Use WebSockets for real-time monitoring:

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app)

def broadcast_pipeline_update(pipeline_id: str, status: str):
    socketio.emit('pipeline_update', {
        'pipeline_id': pipeline_id,
        'status': status,
        'timestamp': datetime.now().isoformat()
    })
```

## 📚 Additional Resources

- **[Getting Started Guide](getting-started.md)** - Quick start tutorial
- **[User Guide](user-guide.md)** - Comprehensive usage instructions
- **[Configuration Reference](configuration.md)** - Configuration options
- **[CLI Reference](cli-reference.md)** - Command-line interface
- **[API Reference](api-reference.md)** - Core API documentation
- **[Installation Guide](installation.md)** - Installation and deployment

---

**Need help with monitoring?** Check out the [User Guide](user-guide.md) for practical examples or the [Troubleshooting](#troubleshooting) section for common issues.
