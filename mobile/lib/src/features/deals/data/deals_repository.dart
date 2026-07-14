import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/deal.dart';

final dealsRepositoryProvider = Provider<DealsRepository>((ref) {
  return DealsRepository(ref.watch(dioProvider));
});

final dealsProvider = FutureProvider.autoDispose<List<Deal>>((ref) async {
  return ref.watch(dealsRepositoryProvider).listDeals();
});

class DealsRepository {
  const DealsRepository(this._dio);

  final Dio _dio;

  Future<List<Deal>> listDeals({String? stage}) async {
    final response = await _dio.get<List<dynamic>>(
      '/api/v1/deals',
      queryParameters: {if (stage != null) 'stage': stage},
    );
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(Deal.fromJson)
        .toList(growable: false);
  }

  Future<Deal> createDeal({
    required String title,
    String? value,
    String currency = 'TRY',
    String? contactId,
    DateTime? expectedCloseDate,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/deals',
      data: {
        'title': title.trim(),
        'value': _parseValue(value),
        'currency': currency,
        'contact_id': _emptyToNull(contactId),
        'expected_close_date': expectedCloseDate?.toUtc().toIso8601String(),
      },
    );
    return Deal.fromJson(response.data!);
  }

  Future<Deal> updateStage(String dealId, String stage) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/api/v1/deals/$dealId',
      data: {'stage': stage},
    );
    return Deal.fromJson(response.data!);
  }

  double? _parseValue(String? value) {
    final trimmed = value?.trim();
    if (trimmed == null || trimmed.isEmpty) {
      return null;
    }
    return double.tryParse(trimmed.replaceAll(',', '.'));
  }

  String? _emptyToNull(String? value) {
    final trimmed = value?.trim();
    return trimmed == null || trimmed.isEmpty ? null : trimmed;
  }
}
