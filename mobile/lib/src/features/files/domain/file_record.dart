class FileRecord {
  const FileRecord({
    required this.id,
    required this.filename,
    required this.mimeType,
    required this.sizeBytes,
    required this.status,
    required this.createdAt,
  });

  final String id;
  final String filename;
  final String mimeType;
  final int sizeBytes;
  final String status;
  final DateTime createdAt;

  factory FileRecord.fromJson(Map<String, dynamic> json) {
    return FileRecord(
      id: json['id'] as String,
      filename: json['filename'] as String,
      mimeType: json['mime_type'] as String,
      sizeBytes: json['size_bytes'] as int,
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class FileAnalysis {
  const FileAnalysis({
    required this.fileId,
    required this.status,
    this.summary,
  });

  final String fileId;
  final String status;
  final String? summary;

  factory FileAnalysis.fromJson(Map<String, dynamic> json) {
    return FileAnalysis(
      fileId: json['file_id'] as String,
      status: json['status'] as String,
      summary: json['summary'] as String?,
    );
  }
}
