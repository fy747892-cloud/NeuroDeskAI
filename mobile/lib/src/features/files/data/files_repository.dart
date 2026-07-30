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

  Future<FileAnalysis> getAnalysis(String fileId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/files/$fileId/analysis',
    );
    return FileAnalysis.fromJson(response.data!);
  }

  Future<FileText> getText(String fileId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/files/$fileId/text',
    );
    return FileText.fromJson(response.data!);
  }

  Future<String> getDownloadUrl(String fileId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/files/$fileId/download-url',
    );
    return response.data!['download_url'] as String;
  }

}
