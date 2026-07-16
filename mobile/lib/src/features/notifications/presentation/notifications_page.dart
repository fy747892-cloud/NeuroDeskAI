import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../data/notifications_repository.dart';
import '../domain/app_notification.dart';

class NotificationsPage extends ConsumerWidget {
  const NotificationsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationsProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(notificationsProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Bildirimler', style: theme.textTheme.headlineMedium),
          const SizedBox(height: 6),
          Text(
            'Operasyon akisindaki yeni uyari ve hatirlatmalari takip et.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          notifications.when(
            data: (items) => items.isEmpty
                ? const _PageMessage(message: 'Bildirim yok.')
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _NotificationsSummary(notifications: items),
                      const SizedBox(height: 14),
                      ...items.map(
                        (item) => _NotificationTile(notification: item),
                      ),
                    ],
                  ),
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'Bildirimler alinamadi.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

class _NotificationsSummary extends StatelessWidget {
  const _NotificationsSummary({required this.notifications});

  final List<AppNotification> notifications;

  @override
  Widget build(BuildContext context) {
    final unreadCount =
        notifications.where((notification) => !notification.isRead).length;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF35225D),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: _SummaryMetric(
              label: 'Toplam',
              value: notifications.length.toString(),
              icon: Icons.notifications_outlined,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Okunmamis',
              value: unreadCount.toString(),
              icon: Icons.mark_email_unread_outlined,
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

class _NotificationTile extends ConsumerStatefulWidget {
  const _NotificationTile({required this.notification});

  final AppNotification notification;

  @override
  ConsumerState<_NotificationTile> createState() => _NotificationTileState();
}

class _NotificationTileState extends ConsumerState<_NotificationTile> {
  bool _isSubmitting = false;

  @override
  Widget build(BuildContext context) {
    final notification = widget.notification;
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: notification.targetRoute == null || _isSubmitting
            ? null
            : () => _openNotification(notification),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: notification.isRead
                      ? const Color(0xFFF4F5FB)
                      : const Color(0x1A3525CD),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  notification.isRead
                      ? Icons.notifications_none
                      : Icons.notifications_active,
                  color: notification.isRead ? null : colorScheme.primary,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            notification.title,
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ),
                        Chip(
                          label: Text(notification.isRead ? 'Okundu' : 'Yeni'),
                          visualDensity: VisualDensity.compact,
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(notification.body),
                    const SizedBox(height: 8),
                    Text(
                      '${_typeLabel(notification.notificationType)} - ${_formatDate(notification.scheduledAt)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    if (!notification.isRead) ...[
                      const SizedBox(height: 10),
                      Align(
                        alignment: Alignment.centerRight,
                        child: OutlinedButton.icon(
                          onPressed: _isSubmitting ? null : _markRead,
                          icon: _isSubmitting
                              ? const SizedBox.square(
                                  dimension: 16,
                                  child:
                                      CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.done),
                          label: const Text('Okundu'),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _typeLabel(String type) {
    return switch (type.toLowerCase()) {
      'task' => 'Gorev',
      'appointment' => 'Takvim',
      'approval' => 'Onay',
      _ => type,
    };
  }

  String _formatDate(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}.'
        '${local.month.toString().padLeft(2, '0')} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }

  Future<void> _markRead() async {
    setState(() => _isSubmitting = true);
    try {
      await ref
          .read(notificationsRepositoryProvider)
          .markRead(widget.notification.id);
      ref.invalidate(notificationsProvider);
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _openNotification(AppNotification notification) async {
    if (!notification.isRead) {
      await _markRead();
    }
    if (!mounted) {
      return;
    }
    final route = notification.targetRoute;
    if (route != null) {
      context.go(route);
    }
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
