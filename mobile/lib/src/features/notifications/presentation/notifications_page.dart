import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
import '../data/notifications_repository.dart';
import '../domain/app_notification.dart';

class NotificationsPage extends ConsumerWidget {
  const NotificationsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationsProvider);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(notificationsProvider.future),
      child: ListView(
        padding: kScreenPadding,
        children: [
          StitchDetailHeader(
            title: 'Bildirimler',
            onBack: () =>
                context.canPop() ? context.pop() : context.go('/app/dashboard'),
          ),
          const SizedBox(height: 8),
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
              message: readableApiError(error, 'Bildirimler alınamadı.'),
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

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: BentoStatTile(
            icon: Icons.notifications_outlined,
            label: 'Toplam',
            value: notifications.length.toString(),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: InfoTile(
            icon: Icons.mark_email_unread_outlined,
            label: 'Okunmamış',
            text: '$unreadCount okunmamış bildirim',
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

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        padding: const EdgeInsets.all(14),
        onTap: notification.targetRoute == null || _isSubmitting
            ? null
            : () => _openNotification(notification),
        child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: notification.isRead
                      ? colorScheme.surfaceContainer
                      : colorScheme.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
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
    );
  }

  String _typeLabel(String type) {
    return switch (type.toLowerCase()) {
      'task' => 'Görev',
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
    final route = notification.targetRoute;
    setState(() => _isSubmitting = true);
    try {
      if (!notification.isRead) {
        await ref
            .read(notificationsRepositoryProvider)
            .markRead(notification.id);
        ref.invalidate(notificationsProvider);
      }
      if (!mounted) {
        return;
      }
      if (route != null) {
        context.go(route);
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              readableApiError(error, 'Bildirim açılamadı.'),
            ),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return AppCard(child: Text(message));
  }
}
