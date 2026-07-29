import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/notifications/data/notifications_repository.dart';

/// Per-screen header matching the Stitch design: avatar + title on the
/// left, notification bell on the right. Every top-level Stitch screen
/// (Özet, Çağrılar, Görüşmeler, Kişiler, Fırsatlar, Ayarlar, ...) repeats
/// this same header rather than sharing one app-wide bar.
class StitchScreenHeader extends ConsumerWidget {
  const StitchScreenHeader({required this.title, super.key});

  final String title;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationsProvider).valueOrNull ?? const [];
    final unread = notifications.where((item) => !item.isRead).length;
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: theme.colorScheme.primary.withValues(alpha: 0.1),
                child: Icon(Icons.person, color: theme.colorScheme.primary),
              ),
              const SizedBox(width: 12),
              Text(title, style: theme.textTheme.titleLarge),
            ],
          ),
          IconButton(
            tooltip: 'Bildirimler',
            onPressed: () => context.go('/app/notifications'),
            icon: Badge(
              isLabelVisible: unread > 0,
              label: Text(unread > 99 ? '99+' : '$unread'),
              child: Icon(Icons.notifications_outlined,
                  color: theme.colorScheme.primary),
            ),
          ),
        ],
      ),
    );
  }
}

/// Header for detail/sub-screens: back button + title, matching Stitch's
/// "Görüşme Detayı" style header.
class StitchDetailHeader extends StatelessWidget {
  const StitchDetailHeader({
    required this.title,
    required this.onBack,
    super.key,
  });

  final String title;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          IconButton(
            onPressed: onBack,
            icon: const Icon(Icons.arrow_back),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: Text(
              title,
              style: theme.textTheme.titleLarge,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
