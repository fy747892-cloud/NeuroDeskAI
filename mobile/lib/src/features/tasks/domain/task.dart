class Task {
  const Task({
    required this.id,
    required this.title,
    required this.status,
    required this.priority,
    this.description,
    this.dueAt,
  });

  final String id;
  final String title;
  final String status;
  final String priority;
  final String? description;
  final DateTime? dueAt;

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      status: json['status'] as String,
      priority: json['priority'] as String,
      dueAt: json['due_at'] == null ? null : DateTime.parse(json['due_at'] as String),
    );
  }
}
