"""
Red Hat Status Checker - Data Models

This module contains all the data structures and models used throughout
the Red Hat Status monitoring system. It includes:

- Performance tracking metrics
- Service health monitoring structures  
- Alert and notification models
- AI analytics and anomaly detection data
- SLO/SLA tracking structures

Author: Red Hat Status Checker v3.0 - Modular Edition
Version: 3.1.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    AVAILABILITY_DROP = "availability_drop"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SERVICE_FLAPPING = "service_flapping"
    UNUSUAL_BEHAVIOR = "unusual_behavior"
    RESPONSE_TIME_SPIKE = "response_time_spike"
    ERROR_RATE_INCREASE = "error_rate_increase"


class InsightType(Enum):
    """Types of predictive insights"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CAPACITY_PLANNING = "capacity_planning"
    MAINTENANCE_REQUIRED = "maintenance_required"
    ANOMALY_FORECAST = "anomaly_forecast"


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics for system monitoring"""
    start_time: datetime
    end_time: Optional[datetime] = None
    api_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    response_time: float = 0.0
    data_size: int = 0
    errors: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def duration(self) -> float:
        """Calculate operation duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio percentage"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0


@dataclass
class ServiceHealthMetrics:
    """Service health analysis and monitoring data"""
    name: str
    status: str
    last_seen: datetime
    uptime_percentage: float = 0.0
    avg_response_time: float = 0.0
    error_count: int = 0
    trend: str = "stable"  # improving, degrading, stable
    criticality: str = "normal"  # critical, high, normal, low


@dataclass
class SystemAlert:
    """System alert structure for notifications"""
    timestamp: datetime
    severity: str  # critical, warning, info
    component: str
    message: str
    acknowledged: bool = False
    auto_resolved: bool = False


@dataclass
class AnomalyDetection:
    """Detected anomaly information"""
    timestamp: datetime
    service_name: str
    anomaly_type: AnomalyType
    severity: AlertSeverity
    description: str
    confidence_score: float
    affected_metrics: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass 
class PredictiveInsight:
    """Predictive analytics insight"""
    timestamp: datetime
    service_name: str
    insight_type: InsightType
    description: str
    confidence_score: float
    time_horizon_hours: int
    predicted_values: Dict[str, Any] = field(default_factory=dict)
    actionable: bool = True
    impact_score: float = 0.0


@dataclass 
class PredictiveAlert:
    """Predictive failure analysis and forecasting"""
    component_name: str
    predicted_failure_time: datetime
    probability: float
    risk_factors: List[str]
    mitigation_steps: List[str]
    confidence_level: str  # low, medium, high
    

@dataclass
class ServiceLevelObjective:
    """SLA/SLO tracking and monitoring"""
    service_name: str
    target_availability: float  # 99.9%
    current_availability: float
    monthly_downtime_budget: timedelta
    consumed_downtime: timedelta
    slo_status: str  # meeting, at_risk, breached
    days_remaining: int


@dataclass
class HealthReport:
    """Comprehensive system health report"""
    timestamp: datetime
    overall_health_score: float
    availability_percentage: float
    total_services: int
    operational_services: int
    services_with_issues: int
    performance_grade: str
    alerts: List[SystemAlert]
    recommendations: List[str]
    slo_status: Dict[str, Any]
    
    @property
    def health_grade(self) -> str:
        """Convert health score to letter grade"""
        if self.overall_health_score >= 99.9:
            return "A+"
        elif self.overall_health_score >= 99.5:
            return "A"
        elif self.overall_health_score >= 95.0:
            return "B"
        elif self.overall_health_score >= 90.0:
            return "C"
        else:
            return "F"


@dataclass
class CacheInfo:
    """Cache system information and statistics"""
    enabled: bool
    size_bytes: int
    hit_ratio: float
    entries_count: int
    ttl_seconds: int
    compression_enabled: bool
    last_cleanup: datetime
    
    @property
    def size_human(self) -> str:
        """Human-readable cache size"""
        if self.size_bytes > 1024 * 1024:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"
        elif self.size_bytes > 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_bytes} bytes"


@dataclass
class APIResponse:
    """Standardized API response structure"""
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    response_time: float
    status_code: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_valid(self) -> bool:
        """Check if response contains valid data"""
        return self.success and self.data is not None


# Type aliases for better code readability
StatusData = Dict[str, Any]
ComponentList = List[Dict[str, Any]]
ConfigDict = Dict[str, Any]
MetricsDict = Dict[str, Union[int, float, str]]
