class Conversation {
  const Conversation({
    required this.id,
    required this.title,
    required this.sourceType,
    required this.status,
    required this.createdAt,
  });

  final String id;
  final String title;
  final String sourceType;
  final String status;
  final DateTime createdAt;

  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      id: json['id'] as String,
      title: json['title'] as String,
      sourceType: json['source_type'] as String,
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class CallTextResult {
  const CallTextResult({required this.conversationId});

  final String conversationId;

  factory CallTextResult.fromJson(Map<String, dynamic> json) {
    final conversation = json['conversation'] as Map<String, dynamic>;
    return CallTextResult(conversationId: conversation['id'] as String);
  }
}

class ConversationDetail {
  const ConversationDetail({
    required this.id,
    required this.title,
    required this.sourceType,
    required this.status,
    required this.createdAt,
    required this.participantNames,
    required this.calls,
  });

  final String id;
  final String title;
  final String sourceType;
  final String status;
  final DateTime createdAt;
  final List<String> participantNames;
  final List<ConversationCall> calls;

  factory ConversationDetail.fromJson(Map<String, dynamic> json) {
    return ConversationDetail(
      id: json['id'] as String,
      title: json['title'] as String,
      sourceType: json['source_type'] as String,
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      participantNames: ((json['participants'] as List<dynamic>?) ?? const [])
          .cast<Map<String, dynamic>>()
          .map((item) => item['display_name'] as String)
          .toList(growable: false),
      calls: ((json['calls'] as List<dynamic>?) ?? const [])
          .cast<Map<String, dynamic>>()
          .map(ConversationCall.fromJson)
          .toList(growable: false),
    );
  }
}

class ConversationCall {
  const ConversationCall({
    required this.id,
    required this.transcripts,
    this.phoneNumber,
    this.durationSeconds,
  });

  final String id;
  final String? phoneNumber;
  final int? durationSeconds;
  final List<String> transcripts;

  factory ConversationCall.fromJson(Map<String, dynamic> json) {
    return ConversationCall(
      id: json['id'] as String,
      phoneNumber: json['phone_number'] as String?,
      durationSeconds: json['duration_seconds'] as int?,
      transcripts: ((json['transcriptions'] as List<dynamic>?) ?? const [])
          .cast<Map<String, dynamic>>()
          .map((item) => item['transcript_text'] as String)
          .toList(growable: false),
    );
  }
}
