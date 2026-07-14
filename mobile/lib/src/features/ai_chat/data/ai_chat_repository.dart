import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../domain/chat_message.dart';

final aiChatRepositoryProvider = Provider<AiChatRepository>((ref) {
  return AiChatRepository(ref.watch(dioProvider));
});

class AiChatRepository {
  const AiChatRepository(this._dio);

  final Dio _dio;

  Future<List<ChatSession>> listSessions() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/ai/chat/sessions');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(ChatSession.fromJson)
        .toList(growable: false);
  }

  Future<ChatSessionDetail> getSession(String sessionId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/ai/chat/sessions/$sessionId',
    );
    return ChatSessionDetail.fromJson(response.data!);
  }

  Future<ChatMessage> sendMessage({
    required String message,
    String? sessionId,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/ai/chat',
      data: {
        'message': message,
        if (sessionId != null) 'session_id': sessionId,
      },
    );
    return ChatMessage.fromJson(response.data!);
  }
}
