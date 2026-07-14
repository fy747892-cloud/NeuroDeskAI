import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../data/ai_chat_repository.dart';
import '../domain/chat_message.dart';

final aiChatControllerProvider =
    AsyncNotifierProvider<AiChatController, AiChatState>(
  AiChatController.new,
);

class AiChatState {
  const AiChatState({
    required this.sessions,
    required this.messages,
    this.activeSessionId,
    this.errorMessage,
    this.isSending = false,
  });

  final List<ChatSession> sessions;
  final List<ChatMessage> messages;
  final String? activeSessionId;
  final String? errorMessage;
  final bool isSending;

  AiChatState copyWith({
    List<ChatSession>? sessions,
    List<ChatMessage>? messages,
    String? activeSessionId,
    String? errorMessage,
    bool? isSending,
  }) {
    return AiChatState(
      sessions: sessions ?? this.sessions,
      messages: messages ?? this.messages,
      activeSessionId: activeSessionId ?? this.activeSessionId,
      errorMessage: errorMessage,
      isSending: isSending ?? this.isSending,
    );
  }
}

class AiChatController extends AsyncNotifier<AiChatState> {
  @override
  Future<AiChatState> build() async {
    final sessions = await ref.read(aiChatRepositoryProvider).listSessions();
    return AiChatState(sessions: sessions, messages: const []);
  }

  Future<void> refreshSessions() async {
    final current = state.valueOrNull;
    if (current == null) {
      ref.invalidateSelf();
      return;
    }

    state = AsyncData(current.copyWith(errorMessage: null));
    try {
      final sessions = await ref.read(aiChatRepositoryProvider).listSessions();
      state = AsyncData(current.copyWith(sessions: sessions));
    } catch (error) {
      state = AsyncData(
        current.copyWith(
          errorMessage: readableApiError(error, 'Chat oturumlari alinamadi.'),
        ),
      );
    }
  }

  Future<void> openSession(String sessionId) async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    state = AsyncData(current.copyWith(errorMessage: null));
    try {
      final detail = await ref.read(aiChatRepositoryProvider).getSession(
            sessionId,
          );
      state = AsyncData(
        current.copyWith(
          activeSessionId: detail.id,
          messages: detail.messages,
        ),
      );
    } catch (error) {
      state = AsyncData(
        current.copyWith(
          errorMessage: readableApiError(error, 'Chat oturumu acilamadi.'),
        ),
      );
    }
  }

  Future<void> send(String text) async {
    final current = state.valueOrNull;
    final message = text.trim();
    if (current == null || message.isEmpty || current.isSending) {
      return;
    }

    final localUserMessage = ChatMessage(
      id: 'local-${DateTime.now().microsecondsSinceEpoch}',
      sessionId: current.activeSessionId ?? 'local',
      role: 'user',
      content: message,
      createdAt: DateTime.now(),
    );

    state = AsyncData(
      current.copyWith(
        messages: [...current.messages, localUserMessage],
        errorMessage: null,
        isSending: true,
      ),
    );

    try {
      final assistantMessage = await ref
          .read(aiChatRepositoryProvider)
          .sendMessage(message: message, sessionId: current.activeSessionId);
      final sessions = await ref.read(aiChatRepositoryProvider).listSessions();
      final latest = state.valueOrNull ?? current;
      state = AsyncData(
        latest.copyWith(
          sessions: sessions,
          activeSessionId: assistantMessage.sessionId,
          messages: [...latest.messages, assistantMessage],
          isSending: false,
        ),
      );
    } catch (error) {
      final latest = state.valueOrNull ?? current;
      state = AsyncData(
        latest.copyWith(
          isSending: false,
          errorMessage: readableApiError(error, 'Mesaj gonderilemedi.'),
        ),
      );
    }
  }

  void startNewChat() {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }
    state = AsyncData(
      current.copyWith(
        activeSessionId: null,
        messages: const [],
        errorMessage: null,
      ),
    );
  }
}
