import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/call_record.dart';

final callsRepositoryProvider = Provider<CallsRepository>((ref) {
  return CallsRepository(ref.watch(dioProvider));
});

final callsProvider = FutureProvider.autoDispose<List<CallRecord>>((ref) {
  return ref.watch(callsRepositoryProvider).listCalls();
});

class CallsRepository {
  const CallsRepository(this._dio);

  final Dio _dio;

  Future<List<CallRecord>> listCalls() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/calls');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(CallRecord.fromJson)
        .toList(growable: false);
  }

  Future<CallTextResult> createFromText({
    required String title,
    required String transcriptText,
    required List<String> participantNames,
    String? callDirection,
    String? phoneNumber,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/calls/text',
      data: {
        'title': title.trim(),
        'transcript_text': transcriptText.trim(),
        'participant_names': participantNames,
        'call_direction': _emptyToNull(callDirection),
        'phone_number': _emptyToNull(phoneNumber),
        'language': 'tr',
      },
    );
    return CallTextResult.fromJson(response.data!);
  }

  Future<void> requestAnalysis(String conversationId) async {
    await _dio.post<void>('/api/v1/ai/analysis/conversations/$conversationId');
  }

  String? _emptyToNull(String? value) {
    final trimmed = value?.trim();
    return trimmed == null || trimmed.isEmpty ? null : trimmed;
  }
}
