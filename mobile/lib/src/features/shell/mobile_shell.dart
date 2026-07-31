import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_status.dart';
import '../../core/l10n/app_language.dart';
import '../dashboard/data/dashboard_repository.dart';

class MobileShell extends ConsumerWidget {
  const MobileShell({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).uri.path;
    final apiStatus = ref.watch(apiStatusProvider);
    final dashboard = ref.watch(dashboardProvider).valueOrNull;
    final strings = appStrings(ref);
    return Scaffold(
      body: Column(
        children: [
          apiStatus.when(
            data: (status) => status.isOk
                ? const SizedBox.shrink()
                : _ApiStatusBanner(
                    strings: strings,
                    statusLabel: status.displayLabel,
                    onRetry: () => ref.invalidate(apiStatusProvider),
                  ),
            error: (error, stackTrace) => _ApiStatusBanner(
              strings: strings,
              statusLabel: strings.connectionError,
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
          NavigationDestination(
            icon: const Icon(Icons.home_outlined),
            selectedIcon: const Icon(Icons.home_filled),
            label: strings.summary,
          ),
          NavigationDestination(
            icon: const Icon(Icons.folder_open_outlined),
            selectedIcon: const Icon(Icons.folder_open_rounded),
            label: strings.content,
          ),
          NavigationDestination(
            icon: _BadgeIcon(
                icon: Icons.check_circle_outline,
                count: dashboard?.summary.openTasksCount ?? 0),
            selectedIcon: _BadgeIcon(
                icon: Icons.check_circle_rounded,
                count: dashboard?.summary.openTasksCount ?? 0),
            label: strings.tasks,
          ),
          NavigationDestination(
            icon: const Icon(Icons.people_outline),
            selectedIcon: const Icon(Icons.people_rounded),
            label: strings.contacts,
          ),
          NavigationDestination(
            icon: const Icon(Icons.apps_outlined),
            selectedIcon: const Icon(Icons.apps_rounded),
            label: strings.more,
          ),
        ],
      ),
    );
  }

  int _selectedIndex(String location) {
    if (location.startsWith('/app/files')) return 1;
    if (location.startsWith('/app/calls')) return 1;
    if (location.startsWith('/app/conversations')) return 4;
    if (location.startsWith('/app/tasks')) return 2;
    if (location.startsWith('/app/contacts')) return 3;
    if (location.startsWith('/app/more')) return 4;
    // Reached only via the Daha Fazla grid, so that tab stays highlighted.
    if (location.startsWith('/app/deals')) return 4;
    if (location.startsWith('/app/appointments')) return 4;
    if (location.startsWith('/app/priority')) return 4;
    if (location.startsWith('/app/analytics')) return 4;
    if (location.startsWith('/app/email')) return 4;
    if (location.startsWith('/app/settings')) return 4;
    return 0;
  }

  String _pathForIndex(int index) {
    return switch (index) {
      1 => '/app/files',
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
  const _ApiStatusBanner(
      {required this.strings, this.statusLabel, this.onRetry});

  final AppStrings strings;
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
              const Icon(Icons.wifi_off_outlined,
                  color: Color(0xFFC2410C), size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  statusLabel == null
                      ? strings.apiWeak()
                      : strings.apiWeak(statusLabel),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: const Color(0xFF9A3412),
                        fontWeight: FontWeight.w700,
                      ),
                ),
              ),
              TextButton(onPressed: onRetry, child: Text(strings.retry)),
            ],
          ),
        ),
      ),
    );
  }
}
