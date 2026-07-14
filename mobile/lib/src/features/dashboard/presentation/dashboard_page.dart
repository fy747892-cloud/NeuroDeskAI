import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../data/dashboard_repository.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(dashboardProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          dashboard.when(
            data: (data) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HeroSummary(
                  openTasks: data.summary.openTasksCount,
                  appointments: data.summary.upcomingAppointmentsCount,
                  approvals: data.summary.pendingAiApprovalsCount,
                ),
                const SizedBox(height: 18),
                Text(
                  'Calisma ozeti',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                GridView.count(
                  crossAxisCount:
                      MediaQuery.sizeOf(context).width > 640 ? 4 : 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  children: [
                    _MetricCard(
                      icon: Icons.checklist,
                      accent: const Color(0xFF3525CD),
                      label: 'Acik gorev',
                      value: data.summary.openTasksCount,
                      onTap: () => context.go('/app/tasks'),
                    ),
                    _MetricCard(
                      icon: Icons.warning_amber,
                      accent: const Color(0xFFDC6465),
                      label: 'Gecikmis',
                      value: data.summary.overdueTasksCount,
                      onTap: () => context.go('/app/tasks'),
                    ),
                    _MetricCard(
                      icon: Icons.calendar_today,
                      accent: const Color(0xFF4B6BFB),
                      label: 'Randevu',
                      value: data.summary.upcomingAppointmentsCount,
                      onTap: () => context.go('/app/appointments'),
                    ),
                    _MetricCard(
                      icon: Icons.auto_awesome,
                      accent: const Color(0xFF8B5CF6),
                      label: 'AI onay',
                      value: data.summary.pendingAiApprovalsCount,
                      onTap: () => context.go('/app/approvals'),
                    ),
                  ],
                ),
              ],
            ),
            error: (error, stackTrace) => const _PageMessage(
              title: 'Dashboard alinamadi',
              body: 'Baglantiyi kontrol edip tekrar dene.',
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

class _HeroSummary extends StatelessWidget {
  const _HeroSummary({
    required this.openTasks,
    required this.appointments,
    required this.approvals,
  });

  final int openTasks;
  final int appointments;
  final int approvals;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withValues(alpha: 0.92)),
        gradient: const LinearGradient(
          colors: [Color(0xFFFFFFFF), Color(0xFFF3F0FF)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x1C1F203E),
            blurRadius: 34,
            offset: Offset(0, 16),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
            decoration: BoxDecoration(
              color: const Color(0x1A3525CD),
              borderRadius: BorderRadius.circular(999),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.auto_awesome, size: 16, color: Color(0xFF3525CD)),
                SizedBox(width: 7),
                Text(
                  'AKILLI OZET',
                  style: TextStyle(
                    color: Color(0xFF3525CD),
                    fontSize: 12,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Bugun $appointments randevun, $approvals bekleyen AI onayin ve $openTasks acik gorevin var.',
            style: theme.textTheme.headlineMedium,
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: () => context.go('/app/conversations'),
            icon: const Icon(Icons.bolt),
            label: const Text('Gorusme ekle'),
          ),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.icon,
    required this.accent,
    required this.label,
    required this.value,
    required this.onTap,
  });

  final IconData icon;
  final Color accent;
  final String label;
  final int value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      color: accent.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(icon, color: accent, size: 19),
                  ),
                  const Spacer(),
                  const Icon(Icons.chevron_right, size: 20),
                ],
              ),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '$value',
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                        Text(label,
                            style: Theme.of(context).textTheme.labelLarge),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.title, required this.body});

  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 6),
            Text(body),
          ],
        ),
      ),
    );
  }
}
