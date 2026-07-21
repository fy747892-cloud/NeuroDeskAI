import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../ai_approvals/data/ai_approvals_repository.dart';
import '../../calls/data/calls_repository.dart';
import '../../calls/domain/ai_analysis_job.dart';
import '../../calls/domain/call_record.dart';
import '../data/dashboard_repository.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    final jobs = ref.watch(callAnalysisJobsProvider);
    final calls = ref.watch(callsProvider);
    final approvals = ref.watch(pendingAiApprovalsProvider);

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
                  'Çalışma özeti',
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
                      label: 'Açık görev',
                      value: data.summary.openTasksCount,
                      onTap: () => context.go('/app/tasks'),
                    ),
                    _MetricCard(
                      icon: Icons.warning_amber,
                      accent: const Color(0xFFDC6465),
                      label: 'Gecikmiş',
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
                      label: 'AI onayı',
                      value: data.summary.pendingAiApprovalsCount,
                      onTap: () => context.go('/app/approvals'),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                _ProcessingQueue(
                  jobs: jobs.valueOrNull ?? const [],
                  approvalsCount: data.summary.pendingAiApprovalsCount,
                ),
                const SizedBox(height: 18),
                _RecentActivity(
                  calls: calls.valueOrNull ?? const [],
                  jobs: jobs.valueOrNull ?? const [],
                  approvalsCount: approvals.valueOrNull?.length ??
                      data.summary.pendingAiApprovalsCount,
                ),
              ],
            ),
            error: (error, stackTrace) => const _PageMessage(
              title: 'Dashboard alınamadı',
              body: 'Bağlantıyı kontrol edip tekrar dene.',
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
                  'AKILLI ÖZET',
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
            'Bugün $appointments randevun, $approvals bekleyen AI onayın ve $openTasks açık görevin var.',
            style: theme.textTheme.headlineMedium,
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: () => context.go('/app/conversations'),
            icon: const Icon(Icons.bolt),
            label: const Text('Görüşme ekle'),
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

class _ProcessingQueue extends StatelessWidget {
  const _ProcessingQueue({
    required this.jobs,
    required this.approvalsCount,
  });

  final List<AiAnalysisJob> jobs;
  final int approvalsCount;

  @override
  Widget build(BuildContext context) {
    final activeJobs = jobs
        .where((job) => job.isPending || job.isFailed)
        .toList(growable: false);
    final total = activeJobs.length + approvalsCount;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.sync, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    total == 0 ? 'Devam eden işlem yok' : '$total işlem dikkat bekliyor',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                TextButton(
                  onPressed: () => context.go('/app/approvals'),
                  child: const Text('Onaylar'),
                ),
              ],
            ),
            if (activeJobs.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...activeJobs.take(3).map(
                    (job) => _ActivityLine(
                      icon: job.isFailed ? Icons.error_outline : Icons.auto_awesome,
                      title: job.isFailed ? 'AI analizi başarısız' : 'AI analizi işleniyor',
                      subtitle: job.errorMessage ?? _formatDateTime(job.createdAt),
                      route: '/app/calls',
                    ),
                  ),
            ],
            if (approvalsCount > 0)
              _ActivityLine(
                icon: Icons.verified_outlined,
                title: '$approvalsCount AI onayı bekliyor',
                subtitle: 'Görev, randevu veya fırsat önerilerini incele',
                route: '/app/approvals',
              ),
          ],
        ),
      ),
    );
  }
}

class _RecentActivity extends StatelessWidget {
  const _RecentActivity({
    required this.calls,
    required this.jobs,
    required this.approvalsCount,
  });

  final List<CallRecord> calls;
  final List<AiAnalysisJob> jobs;
  final int approvalsCount;

  @override
  Widget build(BuildContext context) {
    final recent = <_ActivityLine>[
      ...calls.take(3).map(
            (call) => _ActivityLine(
              icon: Icons.call_outlined,
              title: 'Çağrı transkripti oluştu',
              subtitle: call.transcriptions.isEmpty
                  ? _formatDateTime(call.createdAt)
                  : call.transcriptions.first.transcriptText,
              route: '/app/calls',
              sortKey: call.createdAt,
            ),
          ),
      ...jobs.where((job) => job.isCompleted).take(3).map(
            (job) => _ActivityLine(
              icon: Icons.check_circle_outline,
              title: 'AI analizi tamamlandı',
              subtitle: job.summary ?? _formatDateTime(job.createdAt),
              route: '/app/calls',
              sortKey: job.createdAt,
            ),
          ),
    ]..sort(
        (a, b) => (b.sortKey ?? DateTime(0)).compareTo(a.sortKey ?? DateTime(0)),
      );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Son işlemler', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 10),
            if (recent.isEmpty && approvalsCount == 0)
              const Text('Henüz yeni işlem yok.')
            else ...[
              if (approvalsCount > 0)
                _ActivityLine(
                  icon: Icons.auto_awesome,
                  title: 'Yeni AI önerileri hazır',
                  subtitle: '$approvalsCount öneri Onay Merkezi’nde',
                  route: '/app/approvals',
                ),
              ...recent.take(5),
            ],
          ],
        ),
      ),
    );
  }
}

class _ActivityLine extends StatelessWidget {
  const _ActivityLine({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.route,
    this.sortKey,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final String route;
  final DateTime? sortKey;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(
        subtitle,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => context.go(route),
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

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
