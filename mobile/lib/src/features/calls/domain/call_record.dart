class CallRecord {
  const CallRecord({
    required this.id,
    required this.conversationId,
    required this.status,
    required this.createdAt,
    required this.transcriptions,
    this.callDirection,
    this.phoneNumber,
    this.startedAt,
    this.durationSeconds,
  });

  final String id;
  final String conversationId;
  final String? callDirection;
  final String? phoneNumber;
  final DateTime? startedAt;
  final int? durationSeconds;
  final String status;
  final DateTime createdAt;
  final List<CallTranscription> transcriptions;

  factory CallRecord.fromJson(Map<String, dynamic> json) {
    return CallRecord(
      id: json['id'] as String,
      conversationId: json['conversation_id'] as String,
      callDirection: json['call_direction'] as String?,
      phoneNumber: json['phone_number'] as String?,
      startedAt: json['started_at'] == null
          ? null
          : DateTime.parse(json['started_at'] as String),
      durationSeconds: json['duration_seconds'] as int?,
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      transcriptions: (json['transcriptions'] as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(CallTranscription.fromJson)
          .toList(growable: false),
    );
  }
}

class CallTranscription {
  const CallTranscription({
    required this.id,
    required this.callId,
    required this.status,
    required this.transcriptText,
    required this.createdAt,
    this.language,
  });

  final String id;
  final String callId;
  final String? language;
  final String status;
  final String transcriptText;
  final DateTime createdAt;

  factory CallTranscription.fromJson(Map<String, dynamic> json) {
    return CallTranscription(
      id: json['id'] as String,
      callId: json['call_id'] as String,
      language: json['language'] as String?,
      status: json['status'] as String,
      transcriptText: json['transcript_text'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class CallTextResult {
  const CallTextResult({
    required this.conversationId,
    required this.callId,
  });

  final String conversationId;
  final String callId;

  factory CallTextResult.fromJson(Map<String, dynamic> json) {
    final conversation = json['conversation'] as Map<String, dynamic>;
    final call = json['call'] as Map<String, dynamic>;
    return CallTextResult(
      conversationId: conversation['id'] as String,
      callId: call['id'] as String,
    );
  }
}
