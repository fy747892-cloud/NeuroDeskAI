import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_status.dart';
import '../auth/presentation/auth_controller.dart';
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
      if (matchingJobs.isEmpty) {
        return true;
      }
      final latest = matchingJobs.first;
      return latest.isPending || latest.isFailed;
    }).length;
    // Activates the auto phone-state → call-recording listener for as long
    // as the authenticated app shell is mounted; see call_state_listener.dart.
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
            const Text(
              'NeuroDesk AI',
              style: TextStyle(fontWeight: FontWeight.w800),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'AI Chat',
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
            icon: _BadgeIcon(
              icon: Icons.notifications_outlined,
              count: unreadNotifications,
            ),
            onPressed: () => context.go('/app/notifications'),
          ),
          PopupMenuButton<_ShellAction>(
            tooltip: 'Diğer',
            icon: const Icon(Icons.more_vert),
            onSelected: (action) {
              switch (action) {
                case _ShellAction.contacts:
                  context.go('/app/contacts');
                case _ShellAction.conversations:
                  context.go('/app/conversations');
                case _ShellAction.deals:
                  context.go('/app/deals');
                case _ShellAction.priority:
                  context.go('/app/priority');
                case _ShellAction.analytics:
                  context.go('/app/analytics');
                case _ShellAction.files:
                  context.go('/app/files');
                case _ShellAction.email:
                  context.go('/app/email');
                case _ShellAction.settings:
                  context.go('/app/settings');
                case _ShellAction.logout:
                  ref.read(authControllerProvider.notifier).logout();
              }
            },
            itemBuilder: (context) => const [
              PopupMenuItem(
                value: _ShellAction.contacts,
                child: ListTile(
                  leading: Icon(Icons.people_alt_outlined),
                  title: Text('Kişiler'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.conversations,
                child: ListTile(
                  leading: Icon(Icons.forum_outlined),
                  title: Text('Görüşmeler'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.deals,
                child: ListTile(
                  leading: Icon(Icons.account_tree_outlined),
                  title: Text('Fırsatlar'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.priority,
                child: ListTile(
                  leading: Icon(Icons.priority_high),
                  title: Text('Öncelik'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.analytics,
                child: ListTile(
                  leading: Icon(Icons.insights_outlined),
                  title: Text('Analitik'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.files,
                child: ListTile(
                  leading: Icon(Icons.folder_outlined),
                  title: Text('Dosyalar'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.email,
                child: ListTile(
                  leading: Icon(Icons.mail_outline),
                  title: Text('E-posta'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.settings,
                child: ListTile(
                  leading: Icon(Icons.settings_outlined),
                  title: Text('Ayarlar'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.logout,
                child: ListTile(
                  leading: Icon(Icons.logout),
                  title: Text('Çıkış yap'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
            ],
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
          NavigationDestination(
            icon: const Icon(Icons.dashboard_outlined),
            selectedIcon: const Icon(Icons.dashboard),
            label: 'Özet',
          ),
          NavigationDestination(
            icon: _BadgeIcon(
              icon: Icons.checklist_outlined,
              count: dashboard?.summary.openTasksCount ?? 0,
            ),
            selectedIcon: _BadgeIcon(
              icon: Icons.checklist,
              count: dashboard?.summary.openTasksCount ?? 0,
            ),
            label: 'Görevler',
          ),
          NavigationDestination(
            icon: _BadgeIcon(
              icon: Icons.call_outlined,
              count: callsNeedingAttention,
            ),
            selectedIcon: _BadgeIcon(
              icon: Icons.call,
              count: callsNeedingAttention,
            ),
            label: 'Çağrı',
          ),
          NavigationDestination(
            icon: _BadgeIcon(
              icon: Icons.calendar_today_outlined,
              count: dashboard?.summary.upcomingAppointmentsCount ?? 0,
            ),
            selectedIcon: _BadgeIcon(
              icon: Icons.calendar_today,
              count: dashboard?.summary.upcomingAppointmentsCount ?? 0,
            ),
            label: 'Takvim',
          ),
          NavigationDestination(
            icon: _BadgeIcon(
              icon: Icons.verified_outlined,
              count: dashboard?.summary.pendingAiApprovalsCount ?? 0,
            ),
            selectedIcon: _BadgeIcon(
              icon: Icons.verified,
              count: dashboard?.summary.pendingAiApprovalsCount ?? 0,
            ),
            label: 'Onay',
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
            _QuickActionTile(
              icon: Icons.call_outlined,
              title: 'Çağrı kaydet',
              route: '/app/calls',
            ),
            _QuickActionTile(
              icon: Icons.upload_file,
              title: 'Dosya yükle',
              route: '/app/files',
            ),
            _QuickActionTile(
              icon: Icons.checklist,
              title: 'Görev ekle',
              route: '/app/tasks',
            ),
            _QuickActionTile(
              icon: Icons.person_add_alt,
              title: 'Kişi ekle',
              route: '/app/contacts',
            ),
            _QuickActionTile(
              icon: Icons.mic_none,
              title: 'Sesli komut',
              route: '/app/search',
            ),
          ],
        ),
      ),
    );
  }
  int _selectedIndex(String location) {
    if (location.startsWith('/app/tasks')) {
      return 1;
    }
    if (location.startsWith('/app/conversations')) {
      return 2;
    }
    if (location.startsWith('/app/calls')) {
      return 2;
    }
    if (location.startsWith('/app/appointments')) {
      return 3;
    }
    if (location.startsWith('/app/approvals')) {
      return 4;
    }
    return 0;
  }

  String _pathForIndex(int index) {
    return switch (index) {
      1 => '/app/tasks',
      2 => '/app/calls',
      3 => '/app/appointments',
      4 => '/app/approvals',
      _ => '/app/dashboard',
    };
  }
}

enum _ShellAction {
  contacts,
  conversations,
  deals,
  priority,
  analytics,
  files,
  email,
  settings,
  logout,
}

class _BadgeIcon extends StatelessWidget {
  const _BadgeIcon({
    required this.icon,
    required this.count,
  });

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
  const _QuickActionTile({
    required this.icon,
    required this.title,
    required this.route,
  });

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
              const Icon(
                Icons.wifi_off_outlined,
                color: Color(0xFFC2410C),
                size: 18,
              ),
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
              TextButton(
                onPressed: onRetry,
                child: const Text('Dene'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
