class AiAnalysisJob {
  const AiAnalysisJob({
    required this.id,
    required this.sourceType,
    required this.sourceId,
    required this.status,
    this.errorMessage,
  });

  final String id;
  final String sourceType;
  final String sourceId;
  final String status;
  final String? errorMessage;

  bool get isFailed => status.toLowerCase() == 'failed';
  bool get isPending =>
      status.toLowerCase() == 'queued' || status.toLowerCase() == 'processing';
  bool get isCompleted => status.toLowerCase() == 'completed';

  factory AiAnalysisJob.fromJson(Map<String, dynamic> json) {
    return AiAnalysisJob(
      id: json['id'] as String,
      sourceType: json['source_type'] as String,
      sourceId: json['source_id'] as String,
      status: json['status'] as String,
      errorMessage: json['error_message'] as String?,
    );
  }
}
