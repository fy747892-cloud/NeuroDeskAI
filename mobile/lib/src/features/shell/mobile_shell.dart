import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../auth/presentation/auth_controller.dart';

class MobileShell extends ConsumerWidget {
  const MobileShell({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).uri.path;

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
                case _ShellAction.deals:
                  context.go('/app/deals');
                case _ShellAction.priority:
                  context.go('/app/priority');
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
      body: child,
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
            icon: Icon(Icons.forum_outlined),
            selectedIcon: Icon(Icons.forum),
            label: 'Gorusme',
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
      2 => '/app/conversations',
      3 => '/app/appointments',
      4 => '/app/approvals',
      _ => '/app/dashboard',
    };
  }
}

enum _ShellAction { contacts, deals, priority, logout }
