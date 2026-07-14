import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/search_result.dart';

final searchRepositoryProvider = Provider<SearchRepository>((ref) {
  return SearchRepository(ref.watch(dioProvider));
});

class SearchRepository {
  const SearchRepository(this._dio);

  final Dio _dio;

  Future<List<SearchResult>> semanticSearch({
    required String query,
    int limit = 10,
  }) async {
    final response = await _dio.post<List<dynamic>>(
      '/api/v1/search/semantic',
      data: {'query': query, 'limit': limit},
    );
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(SearchResult.fromJson)
        .toList(growable: false);
  }
}
