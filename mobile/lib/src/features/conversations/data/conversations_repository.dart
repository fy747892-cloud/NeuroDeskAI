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

final conversationDetailProvider = FutureProvider.autoDispose
    .family<ConversationDetail, String>((ref, conversationId) async {
  return ref
      .watch(conversationsRepositoryProvider)
      .getConversation(conversationId);
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

  Future<ConversationDetail> getConversation(String conversationId) async {
    final response = await _dio
        .get<Map<String, dynamic>>('/api/v1/conversations/$conversationId');
    return ConversationDetail.fromJson(response.data!);
  }
}
