from src.core.models import Metrics, ServiceStatus
import psutil
import json
import time
import random
from datetime import datetime, timezone, timedelta
from collections import deque
import os
import signal
import sys
import threading
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SimpleMonitor:
    def __init__(self, output_file="data/outputs/realtime_metrics.json"):
        self.output_file = output_file
        self.metrics = deque(maxlen=100)
        self.running = True
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()

        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    existing_data = json.load(f)
                    if existing_data:
                        print(f"Found existing data with {len(existing_data)} records")
                        self.metrics.extend(existing_data[-self.metrics.maxlen:])
                    else:
                        print(f"File exists but is empty: {output_file}")
            except Exception as e:
                print(f"Error reading existing file: {e}")
                with open(output_file, 'w') as f:
                    json.dump([], f)
                print(f"Created new empty file: {output_file}")
        else:
            with open(output_file, 'w') as f:
                json.dump([], f)
            print(f"Created new empty file: {output_file}")

    def get_metrics(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent

        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        time_delta = current_time - self.last_net_time

        if time_delta > 0:
            bytes_sent = current_net_io.bytes_sent - self.last_net_io.bytes_sent
            bytes_recv = current_net_io.bytes_recv - self.last_net_io.bytes_recv

            network_out_kbps = (bytes_sent * 8) / (1024 * time_delta)
            network_in_kbps = (bytes_recv * 8) / (1024 * time_delta)
        else:
            network_out_kbps = 0
            network_in_kbps = 0

        self.last_net_io = current_net_io
        self.last_net_time = current_time

        base_temp = 45
        temp = base_temp + (cpu_percent * 0.4)

        base_power = 50
        power = base_power + (cpu_percent * 1.5)

        latency = 0
        io_wait = 5.0
        error_rate = 0.0
        connections = 45

        service_status = {
            "database": "online",
            "api_gateway": "online",
            "cache": "online"
        }

        paris_tz = timezone(timedelta(hours=2))
        current_time = datetime.now(paris_tz)

        metrics = {
            "timestamp": current_time.isoformat(),
            "cpu_usage": round(cpu_percent, 1),
            "memory_usage": round(memory_percent, 1),
            "latency_ms": round(latency, 1),
            "disk_usage": round(disk_percent, 1),
            "network_in_kbps": round(network_in_kbps, 1),
            "network_out_kbps": round(network_out_kbps, 1),
            "io_wait": round(io_wait, 1),
            "thread_count": threading.active_count(),
            "active_connections": connections,
            "error_rate": error_rate,
            "uptime_seconds": int(time.time() - psutil.boot_time()),
            "temperature_celsius": round(temp, 1),
            "power_consumption_watts": round(power, 1),
            "service_status": service_status
        }

        return metrics

    def run(self):
        print("Real-time monitoring started!")
        print(f"Saving metrics to: {self.output_file}")
        print("Press Ctrl+C to stop")
        print("-" * 60)

        def signal_handler(sig, frame):
            print("\n\nStopping monitor...")
            self.running = False
            self.save_metrics()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        while self.running:
            try:
                metric = self.get_metrics()
                self.metrics.append(metric)

                timestamp = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))

                print(f"\r[{timestamp.strftime('%H:%M:%S')}] "
                      f"CPU: {metric['cpu_usage']}% | "
                      f"Mem: {metric['memory_usage']}% | "
                      f"Temp: {metric['temperature_celsius']}°C | "
                      f"Disk: {metric['disk_usage']}% | "
                      f"Net: ↓{metric['network_in_kbps']:.0f} ↑{metric['network_out_kbps']:.0f} kbps | "
                      f"Records: {len(self.metrics)}/100",
                      end='', flush=True)

                self.save_metrics()

                time.sleep(1)

                time.sleep(5)

            except Exception as e:
                print(f"\nError: {e}")
                time.sleep(5)

    def save_metrics(self):
        try:
            with open(self.output_file, 'w') as f:
                json.dump(list(self.metrics), f, indent=2)

            if os.path.exists(self.output_file):
                file_size = os.path.getsize(self.output_file)
                if file_size == 0:
                    print(f"\nWarning: File {self.output_file} is empty after save!")
                    with open(self.output_file, 'w') as f:
                        json.dump(list(self.metrics), f, indent=2)
        except Exception as e:
            print(f"\nError saving metrics: {e}")


if __name__ == "__main__":
    monitor = SimpleMonitor()
    monitor.run()
