import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_status.dart';
import '../calls/data/call_state_listener.dart';
import '../calls/data/calls_repository.dart';
import '../dashboard/data/dashboard_repository.dart';

class MobileShell extends ConsumerWidget {
  const MobileShell({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).uri.path;
    final apiStatus = ref.watch(apiStatusProvider);
    final dashboard = ref.watch(dashboardProvider).valueOrNull;
    final calls = ref.watch(callsProvider).valueOrNull ?? const [];
    final jobs = ref.watch(callAnalysisJobsProvider).valueOrNull ?? const [];
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
          Expanded(child: SafeArea(bottom: false, child: child)),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex(location),
        onDestinationSelected: (index) => context.go(_pathForIndex(index)),
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home_filled),
            label: 'Özet',
          ),
          NavigationDestination(
            icon: _BadgeIcon(icon: Icons.call_outlined, count: callsNeedingAttention),
            selectedIcon: _BadgeIcon(icon: Icons.call_rounded, count: callsNeedingAttention),
            label: 'Çağrılar',
          ),
          NavigationDestination(
            icon: _BadgeIcon(icon: Icons.check_circle_outline, count: dashboard?.summary.openTasksCount ?? 0),
            selectedIcon: _BadgeIcon(icon: Icons.check_circle_rounded, count: dashboard?.summary.openTasksCount ?? 0),
            label: 'Görevler',
          ),
          const NavigationDestination(
            icon: Icon(Icons.people_outline),
            selectedIcon: Icon(Icons.people_rounded),
            label: 'Kişiler',
          ),
          const NavigationDestination(
            icon: Icon(Icons.apps_outlined),
            selectedIcon: Icon(Icons.apps_rounded),
            label: 'Daha Fazla',
          ),
        ],
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
