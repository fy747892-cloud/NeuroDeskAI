import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_status.dart';
import '../auth/presentation/auth_controller.dart';

class MobileShell extends ConsumerWidget {
  const MobileShell({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).uri.path;
    final apiStatus = ref.watch(apiStatusProvider);

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: Row(
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                gradient: const LinearGradient(
                  colors: [Color(0xFF3525CD), Color(0xFF6B38D4)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
              child: const Center(
                child: Text(
                  'N',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                  ),
                ),
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
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () => context.go('/app/notifications'),
          ),
          PopupMenuButton<_ShellAction>(
            tooltip: 'Diger',
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
                  title: Text('Kisiler'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.conversations,
                child: ListTile(
                  leading: Icon(Icons.forum_outlined),
                  title: Text('Gorusmeler'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.deals,
                child: ListTile(
                  leading: Icon(Icons.account_tree_outlined),
                  title: Text('Firsatlar'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: _ShellAction.priority,
                child: ListTile(
                  leading: Icon(Icons.priority_high),
                  title: Text('Oncelik'),
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
                  title: Text('Cikis yap'),
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
                : const _ApiStatusBanner(),
            error: (error, stackTrace) => _ApiStatusBanner(
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
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Ozet',
          ),
          NavigationDestination(
            icon: Icon(Icons.checklist_outlined),
            selectedIcon: Icon(Icons.checklist),
            label: 'Gorevler',
          ),
          NavigationDestination(
            icon: Icon(Icons.call_outlined),
            selectedIcon: Icon(Icons.call),
            label: 'Cagri',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_today_outlined),
            selectedIcon: Icon(Icons.calendar_today),
            label: 'Takvim',
          ),
          NavigationDestination(
            icon: Icon(Icons.verified_outlined),
            selectedIcon: Icon(Icons.verified),
            label: 'Onay',
          ),
        ],
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

class _ApiStatusBanner extends StatelessWidget {
  const _ApiStatusBanner({this.onRetry});

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
                  'API baglantisi zayif. Backend ve ag durumunu kontrol edin.',
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
