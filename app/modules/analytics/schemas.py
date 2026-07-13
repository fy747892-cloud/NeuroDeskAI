from datetime import date as date_type

from pydantic import BaseModel, ConfigDict


class AggregateIn(BaseModel):
    date: date_type | None = None


class AggregateSummaryOut(BaseModel):
    date: date_type
    tasks: dict
    calls: dict
    appointments: dict
    ai: dict


class AnalyticsOverviewOut(BaseModel):
    date_from: date_type
    date_to: date_type
    tasks_created: int
    tasks_completed: int
    tasks_overdue: int
    calls_total: int
    calls_analyzed: int
    appointments_completed: int
    appointments_upcoming: int
    ai_requests: int
    ai_cost_amount: float


class TaskMetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date_type
    created_count: int
    completed_count: int
    overdue_count: int


class CallMetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date_type
    call_count: int
    analyzed_count: int


class AppointmentMetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date_type
    completed_count: int
    upcoming_count: int


class AIMetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date_type
    request_count: int
    cost_amount: float
    avg_latency_ms: float
