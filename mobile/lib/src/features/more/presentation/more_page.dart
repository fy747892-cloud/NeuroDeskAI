import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class MorePage extends StatefulWidget {
  const MorePage({super.key});

  @override
  State<MorePage> createState() => _MorePageState();
}

class _MorePageState extends State<MorePage> {
  final _searchController = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final modules = _modules.where(
      (module) => module.title.toLowerCase().contains(_query.toLowerCase()),
    );

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
      children: [
        TextField(
          controller: _searchController,
          onChanged: (value) => setState(() => _query = value),
          decoration: const InputDecoration(
            hintText: 'Modül veya özellik ara...',
            prefixIcon: Icon(Icons.search),
          ),
        ),
        const SizedBox(height: 20),
        GridView.count(
          crossAxisCount: 2,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: 1.05,
          children: [
            for (final module in modules)
              _ModuleCard(module: module, onTap: () => context.go(module.route)),
          ],
        ),
      ],
    );
  }
}

class _ModuleCard extends StatelessWidget {
  const _ModuleCard({required this.module, required this.onTap});

  final _Module module;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFFE5E7F1)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: module.accent.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(module.icon, color: module.accent, size: 26),
              ),
              const SizedBox(height: 12),
              Text(
                module.title,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 2),
              Text(
                module.subtitle,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Module {
  const _Module({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.accent,
    required this.route,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color accent;
  final String route;
}

const _modules = [
  _Module(
    title: 'Fırsatlar',
    subtitle: 'Satış hattı',
    icon: Icons.account_tree_outlined,
    accent: Color(0xFF059669),
    route: '/app/deals',
  ),
  _Module(
    title: 'Takvim',
    subtitle: 'Randevular',
    icon: Icons.calendar_today_outlined,
    accent: Color(0xFF4F46E5),
    route: '/app/appointments',
  ),
  _Module(
    title: 'Görüşmeler',
    subtitle: 'Sesli notlar',
    icon: Icons.forum_outlined,
    accent: Color(0xFFD97706),
    route: '/app/conversations',
  ),
  _Module(
    title: 'Öncelikler',
    subtitle: 'Kritik görevler',
    icon: Icons.priority_high,
    accent: Color(0xFFE11D48),
    route: '/app/priority',
  ),
  _Module(
    title: 'Analitik',
    subtitle: 'Performans raporu',
    icon: Icons.insights_outlined,
    accent: Color(0xFF2563EB),
    route: '/app/analytics',
  ),
  _Module(
    title: 'E-posta',
    subtitle: 'Bağlı hesaplar',
    icon: Icons.mail_outline,
    accent: Color(0xFF7C3AED),
    route: '/app/email',
  ),
  _Module(
    title: 'Dosyalar',
    subtitle: 'Belgeler',
    icon: Icons.folder_outlined,
    accent: Color(0xFF0891B2),
    route: '/app/files',
  ),
  _Module(
    title: 'Ayarlar',
    subtitle: 'Profil ve güvenlik',
    icon: Icons.settings_outlined,
    accent: Color(0xFF475569),
    route: '/app/settings',
  ),
];
