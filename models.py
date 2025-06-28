# models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Optional


class ServiceStatus(BaseModel):
    database: str
    api_gateway: str
    cache: str


class Metrics(BaseModel):
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    latency_ms: float
    disk_usage: float
    network_in_kbps: float
    network_out_kbps: float
    io_wait: float
    thread_count: int
    active_connections: int
    error_rate: float
    uptime_seconds: int
    temperature_celsius: float
    power_consumption_watts: float
    service_status: ServiceStatus
