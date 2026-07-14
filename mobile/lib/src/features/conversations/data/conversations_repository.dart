import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/conversation.dart';

final conversationsRepositoryProvider =
    Provider<ConversationsRepository>((ref) {
  return ConversationsRepository(ref.watch(dioProvider));
});

final conversationsProvider =
    FutureProvider.autoDispose<List<Conversation>>((ref) async {
  return ref.watch(conversationsRepositoryProvider).listConversations();
});

class ConversationsRepository {
  const ConversationsRepository(this._dio);

  final Dio _dio;

  Future<List<Conversation>> listConversations() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/conversations');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(Conversation.fromJson)
        .toList(growable: false);
  }

  Future<CallTextResult> createCallFromText({
    required String title,
    required String transcriptText,
    required List<String> participantNames,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/calls/text',
      data: {
        'title': title,
        'transcript_text': transcriptText,
        'participant_names': participantNames,
        'language': 'tr',
      },
    );
    return CallTextResult.fromJson(response.data!);
  }

  Future<void> requestAnalysis(String conversationId) async {
    await _dio.post<void>('/api/v1/ai/analysis/conversations/$conversationId');
  }
}
