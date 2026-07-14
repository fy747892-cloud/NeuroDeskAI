import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/chat_message.dart';
import 'ai_chat_controller.dart';

class AiChatPage extends ConsumerStatefulWidget {
  const AiChatPage({super.key});

  @override
  ConsumerState<AiChatPage> createState() => _AiChatPageState();
}

class _AiChatPageState extends ConsumerState<AiChatPage> {
  final _messageController = TextEditingController();

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(aiChatControllerProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: chat.when(
        data: (state) => Column(
          children: [
            Expanded(
              child: RefreshIndicator(
                onRefresh: () => ref
                    .read(aiChatControllerProvider.notifier)
                    .refreshSessions(),
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'AI Chat',
                                style: theme.textTheme.headlineMedium,
                              ),
                              const SizedBox(height: 6),
                              Text(
                                'Gorev, randevu ve gorusme hafizasi uzerinden soru sor.',
                                style: theme.textTheme.bodyMedium,
                              ),
                            ],
                          ),
                        ),
                        IconButton.filledTonal(
                          tooltip: 'Yeni sohbet',
                          onPressed: () => ref
                              .read(aiChatControllerProvider.notifier)
                              .startNewChat(),
                          icon: const Icon(Icons.add_comment_outlined),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    _ChatSummary(state: state),
                    if (state.errorMessage != null) ...[
                      const SizedBox(height: 12),
                      _PageMessage(message: state.errorMessage!),
                    ],
                    const SizedBox(height: 14),
                    _SessionStrip(
                      sessions: state.sessions,
                      activeSessionId: state.activeSessionId,
                    ),
                    const SizedBox(height: 16),
                    if (state.messages.isEmpty)
                      const _EmptyChat()
                    else
                      ...state.messages.map((message) {
                        return _MessageBubble(message: message);
                      }),
                    if (state.isSending) const _TypingBubble(),
                  ],
                ),
              ),
            ),
            _Composer(
              controller: _messageController,
              isSending: state.isSending,
              onSubmit: _submit,
            ),
          ],
        ),
        error: (error, stackTrace) => ListView(
          padding: const EdgeInsets.all(16),
          children: const [
            _PageMessage(message: 'AI Chat yuklenemedi.'),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }

  void _submit() {
    final text = _messageController.text.trim();
    if (text.isEmpty) {
      return;
    }
    _messageController.clear();
    ref.read(aiChatControllerProvider.notifier).send(text);
  }
}

class _ChatSummary extends StatelessWidget {
  const _ChatSummary({required this.state});

  final AiChatState state;

  @override
  Widget build(BuildContext context) {
    final sourceCount = state.messages.fold<int>(
      0,
      (count, message) => count + (message.sources?.length ?? 0),
    );

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF17152F),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: _SummaryMetric(
              label: 'Oturum',
              value: state.sessions.length.toString(),
              icon: Icons.forum_outlined,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Kaynak',
              value: sourceCount.toString(),
              icon: Icons.travel_explore,
            ),
          ),
        ],
      ),
    );
  }
}

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 38,
          height: 38,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: Colors.white, size: 20),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
              ),
              Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white.withValues(alpha: 0.72),
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _SessionStrip extends ConsumerWidget {
  const _SessionStrip({
    required this.sessions,
    required this.activeSessionId,
  });

  final List<ChatSession> sessions;
  final String? activeSessionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (sessions.isEmpty) {
      return const SizedBox.shrink();
    }

    return SizedBox(
      height: 46,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: sessions.length,
        separatorBuilder: (context, index) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final session = sessions[index];
          final isActive = session.id == activeSessionId;

          return ChoiceChip(
            selected: isActive,
            label: Text(session.title ?? 'Yeni sohbet'),
            avatar: const Icon(Icons.chat_bubble_outline, size: 16),
            onSelected: (_) => ref
                .read(aiChatControllerProvider.notifier)
                .openSession(session.id),
          );
        },
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              Icons.auto_awesome,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 10),
            Text(
              'NeuroDesk hafizasi hazir',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 6),
            Text(
              'Bugunku onceliklerimi sirala, acik gorevleri ozetle veya son gorusmelerden takip aksiyonlarini sor.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message});

  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    final alignment = isUser ? Alignment.centerRight : Alignment.centerLeft;
    final color = isUser
        ? Theme.of(context).colorScheme.primary
        : Theme.of(context).colorScheme.surface;
    final textColor =
        isUser ? Colors.white : Theme.of(context).colorScheme.onSurface;

    return Align(
      alignment: alignment,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 340),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(8),
          border: isUser ? null : Border.all(color: const Color(0xFFE5E7F1)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isUser && message.confidence != null) ...[
              _ConfidenceLine(confidence: message.confidence!),
              const SizedBox(height: 8),
            ],
            Text(
              message.content,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: textColor,
                  ),
            ),
            if (message.sources != null && message.sources!.isNotEmpty) ...[
              const SizedBox(height: 10),
              ...message.sources!.take(3).map((source) {
                return _SourceCard(source: source);
              }),
            ],
            const SizedBox(height: 8),
            Text(
              _formatTime(message.createdAt),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: isUser
                        ? Colors.white.withValues(alpha: 0.72)
                        : Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime value) {
    final local = value.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _ConfidenceLine extends StatelessWidget {
  const _ConfidenceLine({required this.confidence});

  final double confidence;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.speed, size: 16, color: Color(0xFF3525CD)),
        const SizedBox(width: 6),
        Text(
          'Guven ${(confidence * 100).round()}%',
          style: Theme.of(context).textTheme.labelMedium,
        ),
      ],
    );
  }
}

class _SourceCard extends StatelessWidget {
  const _SourceCard({required this.source});

  final ChatSource source;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFFF4F5FB),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(source.title, style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 4),
          Text(source.snippet, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

class _TypingBubble extends StatelessWidget {
  const _TypingBubble();

  @override
  Widget build(BuildContext context) {
    return const Align(
      alignment: Alignment.centerLeft,
      child: Padding(
        padding: EdgeInsets.only(bottom: 12),
        child: Chip(
          avatar: SizedBox.square(
            dimension: 14,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          label: Text('Yanit hazirlaniyor'),
        ),
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.isSending,
    required this.onSubmit,
  });

  final TextEditingController controller;
  final bool isSending;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: Color(0xFFE5E7F1))),
        ),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                minLines: 1,
                maxLines: 4,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => onSubmit(),
                decoration: const InputDecoration(
                  hintText: 'Bugun neye odaklanmaliyim?',
                ),
              ),
            ),
            const SizedBox(width: 10),
            IconButton.filled(
              tooltip: 'Gonder',
              onPressed: isSending ? null : onSubmit,
              icon: const Icon(Icons.send),
            ),
          ],
        ),
      ),
    );
  }
}

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(message),
      ),
    );
  }
}
