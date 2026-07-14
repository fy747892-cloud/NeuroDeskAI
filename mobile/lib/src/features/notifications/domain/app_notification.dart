class AppNotification {
  const AppNotification({
    required this.id,
    required this.title,
    required this.body,
    required this.notificationType,
    required this.channel,
    required this.status,
    required this.scheduledAt,
    required this.createdAt,
    this.sourceType,
    this.sourceId,
    this.readAt,
  });

  final String id;
  final String title;
  final String body;
  final String notificationType;
  final String channel;
  final String? sourceType;
  final String? sourceId;
  final String status;
  final DateTime scheduledAt;
  final DateTime? readAt;
  final DateTime createdAt;

  bool get isRead => readAt != null || status == 'read';

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as String,
      title: json['title'] as String,
      body: json['body'] as String,
      notificationType: json['notification_type'] as String,
      channel: json['channel'] as String,
      sourceType: json['source_type'] as String?,
      sourceId: json['source_id'] as String?,
      status: json['status'] as String,
      scheduledAt: DateTime.parse(json['scheduled_at'] as String),
      readAt: json['read_at'] == null
          ? null
          : DateTime.parse(json['read_at'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}
