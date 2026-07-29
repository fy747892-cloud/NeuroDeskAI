import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_status.dart';
import '../calls/data/call_state_listener.dart';
import '../calls/data/calls_repository.dart';
import '../dashboard/data/dashboard_repository.dart';
import '../notifications/data/notifications_repository.dart';

class MobileShell extends ConsumerWidget {
  const MobileShell({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).uri.path;
    final apiStatus = ref.watch(apiStatusProvider);
    final dashboard = ref.watch(dashboardProvider).valueOrNull;
    final notifications = ref.watch(notificationsProvider).valueOrNull ?? const [];
    final calls = ref.watch(callsProvider).valueOrNull ?? const [];
    final jobs = ref.watch(callAnalysisJobsProvider).valueOrNull ?? const [];
    final unreadNotifications = notifications.where((item) => !item.isRead).length;
    final callsNeedingAttention = calls.where((call) {
      final matchingJobs = jobs.where(
        (job) =>
            job.sourceType.toLowerCase() == 'conversation' &&
            job.sourceId == call.conversationId,
      );
      if (matchingJobs.isEmpty) return true;
      final latest = matchingJobs.first;
      return latest.isPending || latest.isFailed;
    }).length;

    ref.watch(callAutoRecordListenerProvider);

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Image.asset(
                'assets/brand/neurodesk_mark.png',
                width: 34,
                height: 34,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 10),
            const Text('NeuroDesk AI', style: TextStyle(fontWeight: FontWeight.w800)),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'AI sohbet',
            icon: const Icon(Icons.auto_awesome),
            onPressed: () => context.go('/app/chat'),
          ),
          IconButton(
            tooltip: 'Arama',
            icon: const Icon(Icons.search),
            onPressed: () => context.go('/app/search'),
          ),
          IconButton(
            tooltip: 'Bildirimler',
            icon: _BadgeIcon(icon: Icons.notifications_outlined, count: unreadNotifications),
            onPressed: () => context.go('/app/notifications'),
          ),
        ],
      ),
      body: Column(
        children: [
          apiStatus.when(
            data: (status) => status.isOk
                ? const SizedBox.shrink()
                : _ApiStatusBanner(
                    statusLabel: status.displayLabel,
                    onRetry: () => ref.invalidate(apiStatusProvider),
                  ),
            error: (error, stackTrace) => _ApiStatusBanner(
              statusLabel: 'Bağlantı hatası',
              onRetry: () => ref.invalidate(apiStatusProvider),
            ),
            loading: () => const SizedBox.shrink(),
          ),
          Expanded(child: child),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex(location),
        onDestinationSelected: (index) => context.go(_pathForIndex(index)),
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Özet',
          ),
          NavigationDestination(
            icon: _BadgeIcon(icon: Icons.call_outlined, count: callsNeedingAttention),
            selectedIcon: _BadgeIcon(icon: Icons.call, count: callsNeedingAttention),
            label: 'Çağrılar',
          ),
          NavigationDestination(
            icon: _BadgeIcon(icon: Icons.checklist_outlined, count: dashboard?.summary.openTasksCount ?? 0),
            selectedIcon: _BadgeIcon(icon: Icons.checklist, count: dashboard?.summary.openTasksCount ?? 0),
            label: 'Görevler',
          ),
          const NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Kişiler',
          ),
          const NavigationDestination(
            icon: Icon(Icons.grid_view_outlined),
            selectedIcon: Icon(Icons.grid_view),
            label: 'Daha Fazla',
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Hızlı işlem',
        onPressed: () => _showQuickActions(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  Future<void> _showQuickActions(BuildContext context) {
    return showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          children: [
            Text('Hızlı işlem', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 10),
            _QuickActionTile(icon: Icons.call_outlined, title: 'Çağrı kaydet', route: '/app/calls'),
            _QuickActionTile(icon: Icons.upload_file, title: 'Dosya yükle', route: '/app/files'),
            _QuickActionTile(icon: Icons.checklist, title: 'Görev ekle', route: '/app/tasks'),
            _QuickActionTile(icon: Icons.person_add_alt, title: 'Kişi ekle', route: '/app/contacts'),
            _QuickActionTile(icon: Icons.mic_none, title: 'Sesli komut', route: '/app/search'),
          ],
        ),
      ),
    );
  }

  int _selectedIndex(String location) {
    if (location.startsWith('/app/calls')) return 1;
    if (location.startsWith('/app/conversations')) return 1;
    if (location.startsWith('/app/tasks')) return 2;
    if (location.startsWith('/app/contacts')) return 3;
    if (location.startsWith('/app/more')) return 4;
    // Reached only via the Daha Fazla grid, so that tab stays highlighted.
    if (location.startsWith('/app/deals')) return 4;
    if (location.startsWith('/app/appointments')) return 4;
    if (location.startsWith('/app/priority')) return 4;
    if (location.startsWith('/app/analytics')) return 4;
    if (location.startsWith('/app/files')) return 4;
    if (location.startsWith('/app/email')) return 4;
    if (location.startsWith('/app/settings')) return 4;
    return 0;
  }

  String _pathForIndex(int index) {
    return switch (index) {
      1 => '/app/calls',
      2 => '/app/tasks',
      3 => '/app/contacts',
      4 => '/app/more',
      _ => '/app/dashboard',
    };
  }
}

class _BadgeIcon extends StatelessWidget {
  const _BadgeIcon({required this.icon, required this.count});

  final IconData icon;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Badge(
      isLabelVisible: count > 0,
      label: Text(count > 99 ? '99+' : count.toString()),
      child: Icon(icon),
    );
  }
}

class _QuickActionTile extends StatelessWidget {
  const _QuickActionTile({required this.icon, required this.title, required this.route});

  final IconData icon;
  final String title;
  final String route;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      trailing: const Icon(Icons.chevron_right),
      onTap: () {
        Navigator.of(context).pop();
        context.go(route);
      },
    );
  }
}

class _ApiStatusBanner extends StatelessWidget {
  const _ApiStatusBanner({this.statusLabel, this.onRetry});

  final String? statusLabel;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0xFFFFF7ED),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            children: [
              const Icon(Icons.wifi_off_outlined, color: Color(0xFFC2410C), size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  statusLabel == null
                      ? 'API bağlantısı zayıf. Backend ve ağ durumunu kontrol edin.'
                      : 'API bağlantısı zayıf: $statusLabel. Backend ve ağ durumunu kontrol edin.',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: const Color(0xFF9A3412),
                        fontWeight: FontWeight.w700,
                      ),
                ),
              ),
              TextButton(onPressed: onRetry, child: const Text('Dene')),
            ],
          ),
        ),
      ),
    );
  }
}
