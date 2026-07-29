import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/app_components.dart';
import '../../appointments/data/appointments_repository.dart';
import '../../deals/data/deals_repository.dart';
import '../../deals/domain/deal.dart';
import '../../email/data/email_repository.dart';
import '../../files/data/files_repository.dart';
import '../../notifications/data/notifications_repository.dart';

class MorePage extends ConsumerStatefulWidget {
  const MorePage({super.key});

  @override
  ConsumerState<MorePage> createState() => _MorePageState();
}

class _MorePageState extends ConsumerState<MorePage> {
  final _searchController = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final notifications = ref.watch(notificationsProvider).valueOrNull ?? const [];
    final unread = notifications.where((item) => !item.isRead).length;

    final deals = ref.watch(dealsProvider).valueOrNull ?? const [];
    final openDeals = deals.where((deal) => openDealStages.contains(deal.stage)).length;

    final today = DateTime.now();
    final appointments = ref
            .watch(appointmentsForMonthProvider(DateTime(today.year, today.month)))
            .valueOrNull ??
        const [];
    final todayAppointments = appointments.where((appointment) {
      final local = appointment.startAt.toLocal();
      return local.year == today.year && local.month == today.month && local.day == today.day;
    }).length;

    final emailAccounts = ref.watch(emailAccountsProvider).valueOrNull ?? const [];
    final files = ref.watch(filesProvider).valueOrNull ?? const [];
    final totalBytes = files.fold<int>(0, (sum, file) => sum + file.sizeBytes);

    final modules = _modules(
      openDeals: openDeals,
      todayAppointments: todayAppointments,
      emailAccountsCount: emailAccounts.length,
      filesSizeLabel: _formatBytes(totalBytes),
    ).where((module) => module.title.toLowerCase().contains(_query.toLowerCase()));

    return ListView(
      padding: kScreenPadding,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('NeuroDesk',
                    style: theme.textTheme.titleLarge?.copyWith(color: theme.colorScheme.primary)),
                Text(
                  'DAHA FAZLA',
                  style: TextStyle(
                    color: theme.colorScheme.outline,
                    fontWeight: FontWeight.w700,
                    fontSize: 11,
                    letterSpacing: 1.2,
                  ),
                ),
              ],
            ),
            IconButton(
              tooltip: 'Bildirimler',
              onPressed: () => context.go('/app/notifications'),
              icon: Badge(
                isLabelVisible: unread > 0,
                label: Text(unread > 99 ? '99+' : '$unread'),
                child: Icon(Icons.notifications_outlined, color: theme.colorScheme.primary),
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
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
        const SizedBox(height: 20),
        _PremiumBanner(theme: theme),
      ],
    );
  }
}

class _PremiumBanner extends StatelessWidget {
  const _PremiumBanner({required this.theme});

  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.colorScheme.primary,
        borderRadius: BorderRadius.circular(kLargeCardRadius),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'NeuroDesk Premium',
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          const Text(
            'Yapay zeka ile toplantı özetleri ve otomatik müşteri takibi için yükseltin.',
            style: TextStyle(color: Colors.white70),
          ),
          const SizedBox(height: 14),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: theme.colorScheme.primary,
            ),
            onPressed: () => context.go('/app/settings'),
            child: const Text('Yükselt'),
          ),
        ],
      ),
    );
  }
}

class _ModuleCard extends StatelessWidget {
  const _ModuleCard({required this.module, required this.onTap});

  final _Module module;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      radius: kLargeCardRadius,
      padding: const EdgeInsets.all(16),
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          TintedIcon(icon: module.icon, color: module.accent, size: 48, radius: 14),
          const SizedBox(height: 12),
          Text(module.title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 2),
          Text(module.subtitle, style: Theme.of(context).textTheme.bodySmall),
        ],
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

List<_Module> _modules({
  required int openDeals,
  required int todayAppointments,
  required int emailAccountsCount,
  required String filesSizeLabel,
}) {
  return [
    _Module(
      title: 'Fırsatlar',
      subtitle: '$openDeals Aktif Takip',
      icon: Icons.stars_rounded,
      accent: const Color(0xFF059669),
      route: '/app/deals',
    ),
    _Module(
      title: 'Takvim',
      subtitle: 'Bugün $todayAppointments Etkinlik',
      icon: Icons.calendar_today_outlined,
      accent: const Color(0xFF4F46E5),
      route: '/app/appointments',
    ),
    _Module(
      title: 'Görüşmeler',
      subtitle: 'Sesli Notlar',
      icon: Icons.forum_outlined,
      accent: const Color(0xFFD97706),
      route: '/app/conversations',
    ),
    _Module(
      title: 'Öncelikler',
      subtitle: 'Kritik Görevler',
      icon: Icons.priority_high,
      accent: const Color(0xFFE11D48),
      route: '/app/priority',
    ),
    _Module(
      title: 'Analitik',
      subtitle: 'Performans Raporu',
      icon: Icons.insights_outlined,
      accent: const Color(0xFF2563EB),
      route: '/app/analytics',
    ),
    _Module(
      title: 'E-posta',
      subtitle: emailAccountsCount == 0 ? 'Hesap bağlı değil' : '$emailAccountsCount Hesap Bağlı',
      icon: Icons.mail_outline,
      accent: const Color(0xFF7C3AED),
      route: '/app/email',
    ),
    _Module(
      title: 'Dosyalar',
      subtitle: filesSizeLabel,
      icon: Icons.folder_open_outlined,
      accent: const Color(0xFF0891B2),
      route: '/app/files',
    ),
    _Module(
      title: 'Ayarlar',
      subtitle: 'Profil ve Güvenlik',
      icon: Icons.settings_outlined,
      accent: const Color(0xFF475569),
      route: '/app/settings',
    ),
    _Module(
      title: 'AI Sohbet',
      subtitle: 'Yapay Zeka Asistanı',
      icon: Icons.auto_awesome,
      accent: const Color(0xFF9333EA),
      route: '/app/chat',
    ),
    _Module(
      title: 'Arama',
      subtitle: 'Her Yerde Ara',
      icon: Icons.search,
      accent: const Color(0xFF0D9488),
      route: '/app/search',
    ),
  ];
}

String _formatBytes(int bytes) {
  if (bytes <= 0) return '0 Dosya';
  const units = ['B', 'KB', 'MB', 'GB'];
  var value = bytes.toDouble();
  var unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex++;
  }
  return '${value.toStringAsFixed(value >= 10 || unitIndex == 0 ? 0 : 1)} ${units[unitIndex]} Kullanıldı';
}
