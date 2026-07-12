class DashboardSummary {
  const DashboardSummary({
    required this.openTasksCount,
    required this.overdueTasksCount,
    required this.upcomingAppointmentsCount,
    required this.pendingAiApprovalsCount,
  });

  final int openTasksCount;
  final int overdueTasksCount;
  final int upcomingAppointmentsCount;
  final int pendingAiApprovalsCount;

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    return DashboardSummary(
      openTasksCount: json['open_tasks_count'] as int,
      overdueTasksCount: json['overdue_tasks_count'] as int,
      upcomingAppointmentsCount: json['upcoming_appointments_count'] as int,
      pendingAiApprovalsCount: json['pending_ai_approvals_count'] as int,
    );
  }
}

class DashboardData {
  const DashboardData({required this.summary, required this.generatedAt});

  final DashboardSummary summary;
  final DateTime generatedAt;

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    return DashboardData(
      summary: DashboardSummary.fromJson(json['summary'] as Map<String, dynamic>),
      generatedAt: DateTime.parse(json['generated_at'] as String),
    );
  }
}
