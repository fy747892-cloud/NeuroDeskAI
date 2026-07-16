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
}
