import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../ai_approvals/data/ai_approvals_repository.dart';
import '../../ai_approvals/domain/ai_action_approval.dart';
import '../../calls/data/calls_repository.dart';
import '../../calls/domain/ai_analysis_job.dart';
import '../../calls/domain/call_record.dart';
import '../../settings/data/settings_repository.dart';
import '../../settings/domain/user_profile.dart';
import '../../tasks/data/tasks_repository.dart';
import '../../tasks/domain/task.dart';
import '../data/dashboard_repository.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    final jobs = ref.watch(callAnalysisJobsProvider);
    final calls = ref.watch(callsProvider);
    final approvals = ref.watch(pendingAiApprovalsProvider);
    final tasks = ref.watch(tasksProvider);
    final currentUser = ref.watch(currentUserProvider).valueOrNull;

    return RefreshIndicator(
      onRefresh: () => ref.refresh(dashboardProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _GreetingRow(name: _firstName(currentUser)),
          const SizedBox(height: 16),
          dashboard.when(
            data: (data) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HeroSummary(
                  openTasks: data.summary.openTasksCount,
                  appointments: data.summary.upcomingAppointmentsCount,
                  approvals: data.summary.pendingAiApprovalsCount,
                ),
                const SizedBox(height: 22),
                _AiSuggestionsSection(
                  approvals: approvals.valueOrNull ?? const [],
                ),
                const SizedBox(height: 22),
                _TodayTasksSection(tasks: tasks.valueOrNull ?? const []),
                const SizedBox(height: 22),
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
            error: (error, stackTrace) => _PageMessage(
              title: 'Özet alınamadı',
              body: readableApiError(
                error,
                'Bağlantıyı kontrol edip tekrar deneyin.',
              ),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

String _firstName(CurrentUser? user) {
  final fullName = user?.profile?.fullName;
  if (fullName != null && fullName.trim().isNotEmpty) {
    return fullName.trim().split(RegExp(r'\s+')).first;
  }
  final email = user?.email;
  if (email != null && email.contains('@')) {
    return email.split('@').first;
  }
  return '';
}

class _GreetingRow extends StatelessWidget {
  const _GreetingRow({required this.name});

  final String name;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        CircleAvatar(
          radius: 20,
          backgroundColor: theme.colorScheme.primary.withValues(alpha: 0.1),
          child: Icon(Icons.person, color: theme.colorScheme.primary),
        ),
        const SizedBox(width: 12),
        Text(
          name.isEmpty ? 'Günaydın' : 'Günaydın $name',
          style: theme.textTheme.titleLarge,
        ),
      ],
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
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(
          colors: [Color(0xFF3525CD), Color(0xFF5D50FE)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x263525CD),
            blurRadius: 24,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Bugün $openTasks görev, $appointments randevu ve $approvals bekleyen önerin var.',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: Colors.white,
                ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              _HeroStat(label: 'Görev', value: openTasks),
              const SizedBox(width: 20),
              _HeroStat(label: 'Randevu', value: appointments),
              const SizedBox(width: 20),
              _HeroStat(label: 'Öneri', value: approvals),
            ],
          ),
        ],
      ),
    );
  }
}

class _HeroStat extends StatelessWidget {
  const _HeroStat({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$value',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.w800,
          ),
        ),
        Text(
          label,
          style: const TextStyle(color: Colors.white70, fontSize: 12),
        ),
      ],
    );
  }
}

class _AiSuggestionsSection extends ConsumerWidget {
  const _AiSuggestionsSection({required this.approvals});

  final List<AiActionApproval> approvals;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (approvals.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Yapay Zeka Önerileri',
                style: Theme.of(context).textTheme.titleMedium),
            TextButton(
              onPressed: () => context.go('/app/calls'),
              child: const Text('Tümünü Gör'),
            ),
          ],
        ),
        SizedBox(
          height: 150,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: approvals.length,
            separatorBuilder: (context, index) => const SizedBox(width: 12),
            itemBuilder: (context, index) =>
                _SuggestionCard(approval: approvals[index]),
          ),
        ),
      ],
    );
  }
}

class _SuggestionCard extends ConsumerStatefulWidget {
  const _SuggestionCard({required this.approval});

  final AiActionApproval approval;

  @override
  ConsumerState<_SuggestionCard> createState() => _SuggestionCardState();
}

class _SuggestionCardState extends ConsumerState<_SuggestionCard> {
  bool _isSubmitting = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      width: 260,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE5E7F1)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0F17152F),
            blurRadius: 20,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(Icons.auto_awesome,
                    size: 18, color: theme.colorScheme.primary),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  widget.approval.displayTitle,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.bodyMedium,
                ),
              ),
            ],
          ),
          const Spacer(),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: _isSubmitting ? null : _reject,
                  child: const Text('Reddet'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: FilledButton(
                  onPressed: _isSubmitting ? null : _approve,
                  child: const Text('Onayla'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _approve() async {
    await _submit(
      () => ref.read(aiApprovalsRepositoryProvider).approve(widget.approval),
    );
  }

  Future<void> _reject() async {
    await _submit(
      () => ref.read(aiApprovalsRepositoryProvider).reject(widget.approval.id),
    );
  }

  Future<void> _submit(Future<Object?> Function() action) async {
    setState(() => _isSubmitting = true);
    try {
      await action();
      ref.invalidate(pendingAiApprovalsProvider);
      ref.invalidate(dashboardProvider);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(readableApiError(error, 'İşlem tamamlanamadı.'))),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}

class _TodayTasksSection extends ConsumerWidget {
  const _TodayTasksSection({required this.tasks});

  final List<Task> tasks;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final now = DateTime.now();
    final today = tasks.where((task) {
      final due = task.dueAt?.toLocal();
      return due != null &&
          due.year == now.year &&
          due.month == now.month &&
          due.day == now.day;
    }).toList(growable: false)
      ..sort((a, b) => (a.dueAt ?? now).compareTo(b.dueAt ?? now));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Bugünün Görevleri',
                style: Theme.of(context).textTheme.titleMedium),
            IconButton(
              onPressed: () => context.go('/app/tasks'),
              icon: const Icon(Icons.add_circle, color: Color(0xFF3525CD)),
            ),
          ],
        ),
        if (today.isEmpty)
          const _PageMessage(
            title: 'Bugün için görev yok',
            body: 'Görevler sekmesinden yeni bir görev ekleyebilirsin.',
          )
        else
          ...today.map((task) => _TodayTaskTile(task: task)),
      ],
    );
  }
}

class _TodayTaskTile extends ConsumerStatefulWidget {
  const _TodayTaskTile({required this.task});

  final Task task;

  @override
  ConsumerState<_TodayTaskTile> createState() => _TodayTaskTileState();
}

class _TodayTaskTileState extends ConsumerState<_TodayTaskTile> {
  bool _isSubmitting = false;

  @override
  Widget build(BuildContext context) {
    final task = widget.task;
    final isCompleted = task.status == 'completed';
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isCompleted ? const Color(0xFFF0EEFB) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE5E7F1)),
      ),
      child: Row(
        children: [
          GestureDetector(
            onTap: isCompleted || _isSubmitting ? null : _complete,
            child: Container(
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                color: isCompleted ? theme.colorScheme.primary : null,
                border: Border.all(
                  color: isCompleted
                      ? theme.colorScheme.primary
                      : const Color(0xFFC7C4D8),
                  width: 2,
                ),
                borderRadius: BorderRadius.circular(6),
              ),
              child: isCompleted
                  ? const Icon(Icons.check, size: 16, color: Colors.white)
                  : null,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  task.title,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    decoration:
                        isCompleted ? TextDecoration.lineThrough : null,
                    color: isCompleted ? theme.colorScheme.outline : null,
                  ),
                ),
                if (task.dueAt != null)
                  Text(
                    isCompleted ? 'Tamamlandı' : _formatTime(task.dueAt!),
                    style: theme.textTheme.bodySmall,
                  ),
              ],
            ),
          ),
          if (!isCompleted)
            IconButton(
              onPressed: () => context.go('/app/tasks/${task.id}'),
              icon: const Icon(Icons.chevron_right),
            ),
        ],
      ),
    );
  }

  Future<void> _complete() async {
    setState(() => _isSubmitting = true);
    try {
      await ref.read(tasksRepositoryProvider).completeTask(widget.task.id);
      ref.invalidate(tasksProvider);
      ref.invalidate(dashboardProvider);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(readableApiError(error, 'Görev tamamlanamadı.'))),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}

String _formatTime(DateTime value) {
  final local = value.toLocal();
  return '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
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
                    total == 0
                        ? 'Devam eden işlem yok'
                        : '$total işlem dikkat bekliyor',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                TextButton(
                  onPressed: () => context.go('/app/calls'),
                  child: const Text('Onaylar'),
                ),
              ],
            ),
            if (activeJobs.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...activeJobs.take(3).map(
                    (job) => _ActivityLine(
                      icon: job.isFailed
                          ? Icons.error_outline
                          : Icons.auto_awesome,
                      title: job.isFailed
                          ? 'AI analizi başarısız'
                          : 'AI analizi işleniyor',
                      subtitle: job.errorMessage == null
                          ? _formatDateTime(job.createdAt)
                          : readableBackendMessage(
                              job.errorMessage,
                              'AI analizi tamamlanamadı.',
                            ),
                      route: '/app/calls',
                    ),
                  ),
            ],
            if (approvalsCount > 0)
              _ActivityLine(
                icon: Icons.verified_outlined,
                title: '$approvalsCount AI onayı bekliyor',
                subtitle: 'Görev, randevu veya fırsat önerilerini incele',
                route: '/app/calls',
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
              subtitle: job.summary == null
                  ? _formatDateTime(job.createdAt)
                  : _localizedAnalysisText(job.summary!),
              route: '/app/calls',
              sortKey: job.createdAt,
            ),
          ),
    ]..sort(
        (a, b) =>
            (b.sortKey ?? DateTime(0)).compareTo(a.sortKey ?? DateTime(0)),
      );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Son işlemler',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 10),
            if (recent.isEmpty && approvalsCount == 0)
              const Text('Henüz yeni işlem yok.')
            else ...[
              if (approvalsCount > 0)
                _ActivityLine(
                  icon: Icons.auto_awesome,
                  title: 'Yeni AI önerileri hazır',
                  subtitle: '$approvalsCount öneri ilgili kartlarda hazır',
                  route: '/app/calls',
                ),
              ...recent.take(5),
            ],
          ],
        ),
      ),
    );
  }
}

String _localizedAnalysisText(String value) {
  final trimmed = value.trim();
  if (trimmed.toLowerCase().startsWith('conversation:')) {
    return 'Görüşme: ${trimmed.substring('conversation:'.length).trim()}';
  }
  return trimmed;
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
