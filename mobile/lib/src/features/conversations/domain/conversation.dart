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
