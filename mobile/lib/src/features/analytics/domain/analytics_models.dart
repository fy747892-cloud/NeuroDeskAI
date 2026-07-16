class AnalyticsOverview {
  const AnalyticsOverview({
    required this.dateFrom,
    required this.dateTo,
    required this.tasksCreated,
    required this.tasksCompleted,
    required this.tasksOverdue,
    required this.callsTotal,
    required this.callsAnalyzed,
    required this.appointmentsCompleted,
    required this.appointmentsUpcoming,
    required this.aiRequests,
    required this.aiCostAmount,
  });

  final DateTime dateFrom;
  final DateTime dateTo;
  final int tasksCreated;
  final int tasksCompleted;
  final int tasksOverdue;
  final int callsTotal;
  final int callsAnalyzed;
  final int appointmentsCompleted;
  final int appointmentsUpcoming;
  final int aiRequests;
  final double aiCostAmount;

  factory AnalyticsOverview.fromJson(Map<String, dynamic> json) {
    return AnalyticsOverview(
      dateFrom: DateTime.parse(json['date_from'] as String),
      dateTo: DateTime.parse(json['date_to'] as String),
      tasksCreated: json['tasks_created'] as int,
      tasksCompleted: json['tasks_completed'] as int,
      tasksOverdue: json['tasks_overdue'] as int,
      callsTotal: json['calls_total'] as int,
      callsAnalyzed: json['calls_analyzed'] as int,
      appointmentsCompleted: json['appointments_completed'] as int,
      appointmentsUpcoming: json['appointments_upcoming'] as int,
      aiRequests: json['ai_requests'] as int,
      aiCostAmount: (json['ai_cost_amount'] as num).toDouble(),
    );
  }
}

class TaskMetric {
  const TaskMetric({
    required this.date,
    required this.createdCount,
    required this.completedCount,
    required this.overdueCount,
  });

  final DateTime date;
  final int createdCount;
  final int completedCount;
  final int overdueCount;

  factory TaskMetric.fromJson(Map<String, dynamic> json) {
    return TaskMetric(
      date: DateTime.parse(json['date'] as String),
      createdCount: json['created_count'] as int,
      completedCount: json['completed_count'] as int,
      overdueCount: json['overdue_count'] as int,
    );
  }
}

class CallMetric {
  const CallMetric({
    required this.date,
    required this.callCount,
    required this.analyzedCount,
  });

  final DateTime date;
  final int callCount;
  final int analyzedCount;

  factory CallMetric.fromJson(Map<String, dynamic> json) {
    return CallMetric(
      date: DateTime.parse(json['date'] as String),
      callCount: json['call_count'] as int,
      analyzedCount: json['analyzed_count'] as int,
    );
  }
}

class AiMetric {
  const AiMetric({
    required this.date,
    required this.requestCount,
    required this.costAmount,
    required this.avgLatencyMs,
  });

  final DateTime date;
  final int requestCount;
  final double costAmount;
  final double avgLatencyMs;

  factory AiMetric.fromJson(Map<String, dynamic> json) {
    return AiMetric(
      date: DateTime.parse(json['date'] as String),
      requestCount: json['request_count'] as int,
      costAmount: (json['cost_amount'] as num).toDouble(),
      avgLatencyMs: (json['avg_latency_ms'] as num).toDouble(),
    );
  }
}

class AnalyticsSnapshot {
  const AnalyticsSnapshot({
    required this.overview,
    required this.taskMetrics,
    required this.callMetrics,
    required this.aiMetrics,
  });

  final AnalyticsOverview overview;
  final List<TaskMetric> taskMetrics;
  final List<CallMetric> callMetrics;
  final List<AiMetric> aiMetrics;
}
