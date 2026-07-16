import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/file_record.dart';

final filesRepositoryProvider = Provider<FilesRepository>((ref) {
  return FilesRepository(ref.watch(dioProvider));
});

final filesProvider = FutureProvider.autoDispose<List<FileRecord>>((ref) {
  return ref.watch(filesRepositoryProvider).listFiles();
});

class FilesRepository {
  const FilesRepository(this._dio);

  final Dio _dio;

  Future<List<FileRecord>> listFiles() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/files');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(FileRecord.fromJson)
        .toList(growable: false);
  }

  Future<FileAnalysis> analyzeFile(String fileId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/files/$fileId/analyze',
    );
    return FileAnalysis.fromJson(response.data!);
  }

  Future<void> deleteFile(String fileId) async {
    await _dio.delete<void>('/api/v1/files/$fileId');
  }

  Future<FileRecord> uploadFile({
    required String filename,
    required String mimeType,
    required int sizeBytes,
    required Stream<List<int>> bytes,
  }) async {
    final startResponse = await _dio.post<Map<String, dynamic>>(
      '/api/v1/files/upload-url',
      data: {
        'filename': filename,
        'mime_type': mimeType,
        'size_bytes': sizeBytes,
      },
    );
    final fileId = startResponse.data!['file_id'] as String;
    final uploadUrl = startResponse.data!['upload_url'] as String;

    await Dio().put<void>(
      uploadUrl,
      data: bytes,
      options: Options(
        contentType: mimeType,
        headers: {'Content-Length': sizeBytes},
      ),
    );

    final completeResponse = await _dio.post<Map<String, dynamic>>(
      '/api/v1/files/complete-upload',
      data: {'file_id': fileId},
    );
    return FileRecord.fromJson(completeResponse.data!);
  }
}
