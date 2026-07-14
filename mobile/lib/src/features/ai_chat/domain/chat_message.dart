class ChatSource {
  const ChatSource({
    required this.sourceType,
    required this.sourceId,
    required this.title,
    required this.snippet,
  });

  final String sourceType;
  final String sourceId;
  final String title;
  final String snippet;

  factory ChatSource.fromJson(Map<String, dynamic> json) {
    return ChatSource(
      sourceType: json['source_type'] as String,
      sourceId: json['source_id'] as String,
      title: json['title'] as String,
      snippet: json['snippet'] as String,
    );
  }
}

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.sessionId,
    required this.role,
    required this.content,
    required this.createdAt,
    this.confidence,
    this.sources,
  });

  final String id;
  final String sessionId;
  final String role;
  final String content;
  final double? confidence;
  final List<ChatSource>? sources;
  final DateTime createdAt;

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] as String,
      sessionId: json['session_id'] as String,
      role: json['role'] as String,
      content: json['content'] as String,
      confidence: (json['confidence'] as num?)?.toDouble(),
      sources: json['sources'] == null
          ? null
          : (json['sources'] as List<dynamic>)
              .cast<Map<String, dynamic>>()
              .map(ChatSource.fromJson)
              .toList(growable: false),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class ChatSession {
  const ChatSession({
    required this.id,
    required this.status,
    required this.createdAt,
    this.title,
  });

  final String id;
  final String? title;
  final String status;
  final DateTime createdAt;

  factory ChatSession.fromJson(Map<String, dynamic> json) {
    return ChatSession(
      id: json['id'] as String,
      title: json['title'] as String?,
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class ChatSessionDetail extends ChatSession {
  const ChatSessionDetail({
    required super.id,
    required super.status,
    required super.createdAt,
    required this.messages,
    super.title,
  });

  final List<ChatMessage> messages;

  factory ChatSessionDetail.fromJson(Map<String, dynamic> json) {
    return ChatSessionDetail(
      id: json['id'] as String,
      title: json['title'] as String?,
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      messages: (json['messages'] as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(ChatMessage.fromJson)
          .toList(growable: false),
    );
  }
}
