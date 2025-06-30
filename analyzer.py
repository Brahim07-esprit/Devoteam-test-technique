import json
from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime
from models import Metrics


class InfrastructureAnalyzer:
    def __init__(self):
        self.thresholds = {
            'cpu': {'warning': 70, 'high': 80, 'critical': 90},
            'memory': {'warning': 70, 'high': 80, 'critical': 90},
            'temperature': {'warning': 60, 'high': 70, 'critical': 80},
            'error_rate': {'warning': 0.02, 'high': 0.05, 'critical': 0.10},
            'latency': {'warning': 200, 'high': 300, 'critical': 500},
            'disk': {'warning': 70, 'high': 80, 'critical': 90}
        }
        self.valid_records = 0
        self.invalid_records = 0
        self.critical_metrics_count = 0
    
    def load_data(self, filepath: str) -> List[Metrics]:
        print("\n=== Data Ingestion Node ===")
        print(f"Loading data from {filepath}...")
        
        with open(filepath, 'r') as f:
            raw_data = json.load(f)
        
        print(f"Loaded {len(raw_data)} records from {filepath}")
        
        metrics = []
        start_time = datetime.now()
        
        print("Processing batches...")
        for i, record in enumerate(raw_data):
            try:
                metric = Metrics(**record)
                metrics.append(metric)
                self.valid_records += 1
                
                if (metric.cpu_usage > 90 or metric.memory_usage > 90 or 
                    metric.temperature_celsius > 80 or metric.error_rate > 0.1 or
                    metric.service_status.api_gateway == 'offline' or
                    metric.service_status.database == 'offline' or
                    metric.service_status.cache == 'offline'):
                    self.critical_metrics_count += 1
                    
            except Exception as e:
                self.invalid_records += 1
                if self.invalid_records <= 3:
                    print(f"  - Validation error in record {i}: {str(e)[:50]}...")
        
        
        print("\nProcessing Complete!")
        print(f"  - Total records: {len(raw_data)}")
        print(f"  - Valid records: {self.valid_records}")
        print(f"  - Invalid records: {self.invalid_records}")
        print(f"  - Critical metrics: {self.critical_metrics_count}")
        
        if metrics:
            timestamps = [m.timestamp for m in metrics]
            start_time = min(timestamps)
            end_time = max(timestamps)
            duration = end_time - start_time
            
            print("\nTime Range:")
            print(f"  - Start: {start_time}")
            print(f"  - End: {end_time}")
            print(f"  - Duration: {duration}")
        
        return metrics
    
    def detect_anomalies(self, metrics: List[Metrics]) -> Dict[str, Any]:
        print("\n=== Anomaly Detection Node ===")
        
        anomalies = []
        service_issues = defaultdict(int)
        severity_count = defaultdict(int)
        anomaly_types = defaultdict(int)
        
        for metric in metrics:
            if metric.cpu_usage >= self.thresholds['cpu']['critical']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'cpu_high',
                    'severity': 'critical',
                    'value': metric.cpu_usage,
                    'description': f'CPU usage critically high at {metric.cpu_usage}%'
                })
                anomaly_types['cpu_high'] += 1
                severity_count['critical'] += 1
            elif metric.cpu_usage >= self.thresholds['cpu']['high']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'cpu_high',
                    'severity': 'high',
                    'value': metric.cpu_usage,
                    'description': f'CPU usage high at {metric.cpu_usage}%'
                })
                anomaly_types['cpu_high'] += 1
                severity_count['high'] += 1

            elif metric.cpu_usage >= self.thresholds['cpu']['warning']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'cpu_high',
                    'severity': 'warning',
                    'value': metric.cpu_usage,
                    'description': f'CPU usage high at {metric.cpu_usage}%'
                })
                anomaly_types['cpu_high'] += 1
                severity_count['warning'] += 1
            
            if metric.memory_usage >= self.thresholds['memory']['critical']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'memory_high',
                    'severity': 'critical',
                    'value': metric.memory_usage,
                    'description': f'Memory usage critically high at {metric.memory_usage}%'
                })
                anomaly_types['memory_high'] += 1
                severity_count['critical'] += 1
            elif metric.memory_usage >= self.thresholds['memory']['high']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'memory_high',
                    'severity': 'high',
                    'value': metric.memory_usage,
                    'description': f'Memory usage high at {metric.memory_usage}%'
                })
                anomaly_types['memory_high'] += 1
                severity_count['high'] += 1

            elif metric.memory_usage >= self.thresholds['memory']['warning']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'memory_high',
                    'severity': 'warning',
                    'value': metric.memory_usage,
                    'description': f'Memory usage high at {metric.memory_usage}%'
                })
                anomaly_types['memory_high'] += 1
                severity_count['warning'] += 1

            if metric.temperature_celsius >= self.thresholds['temperature']['critical']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'temperature_high',
                    'severity': 'critical',
                    'value': metric.temperature_celsius,
                    'description': f'Temperature critically high at {metric.temperature_celsius}°C'
                })
                anomaly_types['temperature_high'] += 1
                severity_count['critical'] += 1
            elif metric.temperature_celsius >= self.thresholds['temperature']['high']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'temperature_high',
                    'severity': 'high',
                    'value': metric.temperature_celsius,
                    'description': f'Temperature high at {metric.temperature_celsius}°C'
                })
                anomaly_types['temperature_high'] += 1
                severity_count['high'] += 1

            elif metric.temperature_celsius >= self.thresholds['temperature']['warning']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'temperature_high',
                    'severity': 'warning',
                    'value': metric.temperature_celsius,
                    'description': f'Temperature high at {metric.temperature_celsius}°C'
                })
                anomaly_types['temperature_high'] += 1
                severity_count['warning'] += 1

            if metric.error_rate >= self.thresholds['error_rate']['critical']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'error_rate_high',
                    'severity': 'critical',
                    'value': metric.error_rate,
                    'description': f'Error rate critically high at {metric.error_rate:.2%}'
                })
                anomaly_types['error_rate_high'] += 1
                severity_count['critical'] += 1
            elif metric.error_rate >= self.thresholds['error_rate']['high']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'error_rate_high',
                    'severity': 'high',
                    'value': metric.error_rate,
                    'description': f'Error rate high at {metric.error_rate:.2%}'
                })
                anomaly_types['error_rate_high'] += 1
                severity_count['high'] += 1

            elif metric.error_rate >= self.thresholds['error_rate']['warning']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'error_rate_high',
                    'severity': 'warning',
                    'value': metric.error_rate,
                    'description': f'Error rate high at {metric.error_rate:.2%}'
                })  
                anomaly_types['error_rate_high'] += 1
                severity_count['warning'] += 1

            if metric.disk_usage >= self.thresholds['disk']['critical']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'disk_high',
                    'severity': 'critical',
                    'value': metric.disk_usage,
                    'description': f'Disk usage critically high at {metric.disk_usage}%'
                })
                anomaly_types['disk_high'] += 1
                severity_count['critical'] += 1

            elif metric.disk_usage >= self.thresholds['disk']['warning']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'disk_high',
                    'severity': 'warning',
                    'value': metric.disk_usage,
                    'description': f'Disk usage high at {metric.disk_usage}%'
                })
                anomaly_types['disk_high'] += 1
                severity_count['warning'] += 1

            if metric.latency_ms >= self.thresholds['latency']['critical']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'latency_high',
                    'severity': 'critical',
                    'value': metric.latency_ms,
                    'description': f'Latency critically high at {metric.latency_ms}ms'
                })
                anomaly_types['latency_high'] += 1
                severity_count['critical'] += 1

            elif metric.latency_ms >= self.thresholds['latency']['warning']:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'latency_high',
                    'severity': 'warning',
                    'value': metric.latency_ms,
                    'description': f'Latency high at {metric.latency_ms}ms'
                })
                anomaly_types['latency_high'] += 1
                severity_count['warning'] += 1

            if metric.service_status.api_gateway == 'offline':
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'service_offline',
                    'severity': 'critical',
                    'value': 0,
                    'description': 'API Gateway is offline'
                })
                anomaly_types['service_offline'] += 1
                severity_count['critical'] += 1
                service_issues['api_gateway'] += 1
            elif metric.service_status.api_gateway == 'degraded':
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'service_degraded',
                    'severity': 'high',
                    'value': 0.5,
                    'description': 'Api Gateway is degraded'
                })
                anomaly_types['service_degraded'] += 1
                severity_count['high'] += 1
                service_issues['api_gateway'] += 1

            elif metric.service_status.api_gateway == 'degraded':
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'service_degraded',
                    'severity': 'warning',
                    'value': 0.5,
                    'description': 'Api Gateway is degraded'
                })
                anomaly_types['service_degraded'] += 1
                severity_count['warning'] += 1
                service_issues['api_gateway'] += 1

            if metric.service_status.database == 'offline':
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'service_offline',
                    'severity': 'critical',
                    'value': 0,
                    'description': 'Database is offline'
                })
                anomaly_types['service_offline'] += 1
                severity_count['critical'] += 1
                service_issues['database'] += 1
            elif metric.service_status.database == 'degraded':
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'service_degraded',
                    'severity': 'high',
                    'value': 0.5,
                    'description': 'Database is degraded'
                })
                anomaly_types['service_degraded'] += 1
                severity_count['high'] += 1
                service_issues['database'] += 1

            elif metric.service_status.database == 'degraded':
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'service_degraded',
                    'severity': 'warning',
                    'value': 0.5,
                    'description': 'Database is degraded'
                })
                anomaly_types['service_degraded'] += 1
                severity_count['warning'] += 1
                service_issues['database'] += 1

            if metric.service_status.cache == 'offline':
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'service_offline',
                    'severity': 'critical',
                    'value': 0,
                    'description': 'Cache is offline'
                })
                anomaly_types['service_offline'] += 1
                severity_count['critical'] += 1
                service_issues['cache'] += 1
            elif metric.service_status.cache == 'degraded':
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'service_degraded',
                    'severity': 'high',
                    'value': 0.5,
                    'description': 'Cache is degraded'
                })
                anomaly_types['service_degraded'] += 1
                severity_count['high'] += 1
                service_issues['cache'] += 1

            elif metric.service_status.cache == 'degraded':
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'service_degraded',
                    'severity': 'warning',
                    'value': 0.5,
                    'description': 'Cache is degraded'
                })
                anomaly_types['service_degraded'] += 1
                severity_count['warning'] += 1
                service_issues['cache'] += 1

            if metric.cpu_usage > 85 and metric.memory_usage > 85:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'resource_exhaustion',
                    'severity': 'critical',
                    'value': (metric.cpu_usage + metric.memory_usage) / 2,
                    'description': 'Resource exhaustion detected (CPU + Memory both > 85%)'
                })
                anomaly_types['resource_exhaustion'] += 1
                severity_count['critical'] += 1
            
            network_total = metric.network_in_kbps + metric.network_out_kbps
            if network_total > 15000 and metric.latency_ms > 200:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'network_saturation',
                    'severity': 'high',
                    'value': network_total,
                    'description': f'Network saturation detected ({network_total} kbps with {metric.latency_ms}ms latency)'
                })
                anomaly_types['network_saturation'] += 1
                severity_count['high'] += 1
            
            if metric.temperature_celsius > 75 and metric.cpu_usage > 80:
                anomalies.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'type': 'temperature_high',
                    'severity': 'high',
                    'value': metric.temperature_celsius,
                    'description': 'Possible thermal throttling (high temp + high CPU)'
                })
                anomaly_types['temperature_high'] += 1
                severity_count['high'] += 1
        
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        
        window_size = 10
        for i in range(len(sorted_metrics) - window_size + 1):
            window = sorted_metrics[i:i + window_size]
            avg_cpu = sum(m.cpu_usage for m in window) / window_size
            if avg_cpu > 85:
                anomalies.append({
                    'timestamp': window[-1].timestamp.isoformat(),
                    'type': 'cpu_trend',
                    'severity': 'medium',
                    'value': avg_cpu,
                    'description': f'Sustained high CPU usage (avg: {avg_cpu:.1f}% over 3 hours)'
                })
                anomaly_types['cpu_trend'] += 1
                severity_count['medium'] += 1
                
                error_rates = [m.error_rate for m in window]
                if all(error_rates[i] <= error_rates[i+1] for i in range(len(error_rates)-1)) and error_rates[-1] > 0.05:
                    anomalies.append({
                        'timestamp': window[-1].timestamp.isoformat(),
                        'type': 'error_rate_high',
                        'severity': 'medium',
                        'value': error_rates[-1],
                        'description': 'Increasing error rate trend detected'
                    })
                    anomaly_types['error_rate_high'] += 1
                    severity_count['medium'] += 1
        
        print("\nAnalysis Complete!")
        print(f"  - Metrics analyzed: {len(metrics)}")
        print(f"  - Anomalies detected: {len(anomalies)}")
        
        print("\nSeverity Distribution:")
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity_count.get(severity, 0) > 0:
                print(f"  - {severity.capitalize()}: {severity_count[severity]}")
        
        print("\nTop Anomaly Types:")
        sorted_types = sorted(anomaly_types.items(), key=lambda x: x[1], reverse=True)[:5]
        for atype, count in sorted_types:
            print(f"  - {atype}: {count}")
        
        if anomalies:
            print("\nSample Anomalies:")
            print("-" * 100)
            print(f"{'Timestamp':<28} {'Type':<18} {'Severity':<10} {'Description'}")
            print("-" * 100)
            for anomaly in anomalies[:5]:
                print(f"{anomaly['timestamp']:<28} {anomaly['type']:<18} {anomaly['severity'].upper():<10} {anomaly['description']}")
        
        return {
            'total_metrics': len(metrics),
            'total_anomalies': len(anomalies),
            'anomaly_breakdown': dict(anomaly_types),
            'service_issues': dict(service_issues),
            'critical_count': severity_count.get('critical', 0),
            'severity_distribution': dict(severity_count),
            'sample_anomalies': anomalies[:10]
        }

if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) != 2:
        print("Usage: python analyzer.py <input_file.json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        sys.exit(1)
    
    print(f"\nAnalyzing infrastructure metrics from {input_file}...")
    
    analyzer = InfrastructureAnalyzer()
    metrics = analyzer.load_data(input_file)
    analysis = analyzer.detect_anomalies(metrics)
    
    print(f"\nAnalysis Summary:")
    print(f"  - Total metrics analyzed: {analysis['total_metrics']}")
    print(f"  - Total anomalies detected: {analysis['total_anomalies']}")
    print(f"  - Critical severity count: {analysis['critical_count']}")
    
    print("\nSeverity Distribution:")
    for severity, count in analysis['severity_distribution'].items():
        print(f"  - {severity.capitalize()}: {count}")
    
    print("\nAnomaly Type Distribution:")
    sorted_types = sorted(analysis['anomaly_breakdown'].items(), key=lambda x: x[1], reverse=True)
    for atype, count in sorted_types[:5]:
        print(f"  - {atype}: {count}")
    
    if analysis['service_issues']:
        print("\nService Issues:")
        for service, count in analysis['service_issues'].items():
            print(f"  - {service}: {count} issues")