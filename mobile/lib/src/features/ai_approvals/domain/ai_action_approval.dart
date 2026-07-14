class AiActionApproval {
  const AiActionApproval({
    required this.id,
    required this.actionType,
    required this.sourceType,
    required this.status,
    required this.suggestedPayload,
    required this.createdAt,
    this.confidenceScore,
    this.expiresAt,
  });

  final String id;
  final String actionType;
  final String sourceType;
  final String status;
  final Map<String, dynamic> suggestedPayload;
  final double? confidenceScore;
  final DateTime? expiresAt;
  final DateTime createdAt;

  factory AiActionApproval.fromJson(Map<String, dynamic> json) {
    return AiActionApproval(
      id: json['id'] as String,
      actionType: json['action_type'] as String,
      sourceType: json['source_type'] as String,
      status: json['status'] as String,
      suggestedPayload: Map<String, dynamic>.from(
        json['suggested_payload'] as Map,
      ),
      confidenceScore: (json['confidence_score'] as num?)?.toDouble(),
      expiresAt: json['expires_at'] == null
          ? null
          : DateTime.parse(json['expires_at'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  String get displayTitle {
    final title = suggestedPayload['title'] ?? suggestedPayload['subject'];
    if (title is String && title.trim().isNotEmpty) {
      return title;
    }
    return switch (actionType) {
      'task' => 'Gorev onerisi',
      'create_task' => 'Gorev onerisi',
      'appointment' => 'Randevu onerisi',
      'create_appointment' => 'Randevu onerisi',
      'deal' => 'Firsat onerisi',
      _ => 'AI aksiyon onerisi',
    };
  }

  String get displayDescription {
    final description =
        suggestedPayload['description'] ?? suggestedPayload['notes'];
    if (description is String && description.trim().isNotEmpty) {
      return description;
    }
    return 'Kaynak: $sourceType';
  }

  String get actionLabel {
    return switch (actionType) {
      'task' => 'Gorev',
      'create_task' => 'Gorev',
      'appointment' => 'Randevu',
      'create_appointment' => 'Randevu',
      'deal' => 'Firsat',
      'send_email' => 'E-posta',
      _ => actionType,
    };
  }
}
