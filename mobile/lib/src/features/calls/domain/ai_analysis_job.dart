class AiAnalysisJob {
  const AiAnalysisJob({
    required this.id,
    required this.sourceType,
    required this.sourceId,
    required this.status,
    required this.results,
    required this.createdAt,
    this.errorMessage,
  });

  final String id;
  final String sourceType;
  final String sourceId;
  final String status;
  final List<AiAnalysisResult> results;
  final DateTime createdAt;
  final String? errorMessage;

  bool get isFailed => status.toLowerCase() == 'failed';
  bool get isPending =>
      status.toLowerCase() == 'queued' || status.toLowerCase() == 'processing';
  bool get isCompleted => status.toLowerCase() == 'completed';

  String? get summary {
    final result = _latestResult('conversation_summary');
    final payload = result?.payload;
    if (payload == null) return null;
    final directSummary = payload['summary'] ?? payload['text'];
    if (directSummary is String && directSummary.trim().isNotEmpty) {
      return directSummary.trim();
    }
    final content = payload.values
        .whereType<String>()
        .map((value) => value.trim())
        .firstWhere((value) => value.isNotEmpty, orElse: () => '');
    return content.isEmpty ? null : content;
  }

  int get suggestedTaskCount => _itemsCount('task_extraction');
  int get suggestedAppointmentCount => _itemsCount('appointment_extraction');
  int get suggestedDealCount => _itemsCount('deal_extraction');

  factory AiAnalysisJob.fromJson(Map<String, dynamic> json) {
    return AiAnalysisJob(
      id: json['id'] as String,
      sourceType: json['source_type'] as String,
      sourceId: json['source_id'] as String,
      status: json['status'] as String,
      results: ((json['results'] as List<dynamic>?) ?? const [])
          .cast<Map<String, dynamic>>()
          .map(AiAnalysisResult.fromJson)
          .toList(growable: false),
      createdAt: DateTime.parse(json['created_at'] as String),
      errorMessage: json['error_message'] as String?,
    );
  }

  AiAnalysisResult? _latestResult(String type) {
    final matches = results.where((result) => result.resultType == type);
    return matches.isEmpty ? null : matches.last;
  }

  int _itemsCount(String type) {
    final items = _latestResult(type)?.payload['items'];
    return items is List ? items.length : 0;
  }
}

class AiAnalysisResult {
  const AiAnalysisResult({
    required this.id,
    required this.resultType,
    required this.payload,
  });

  final String id;
  final String resultType;
  final Map<String, dynamic> payload;

  factory AiAnalysisResult.fromJson(Map<String, dynamic> json) {
    return AiAnalysisResult(
      id: json['id'] as String,
      resultType: json['result_type'] as String,
      payload: (json['result_payload'] as Map<String, dynamic>?) ?? const {},
    );
  }
}
