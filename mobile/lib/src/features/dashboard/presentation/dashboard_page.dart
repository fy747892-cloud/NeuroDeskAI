import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
import '../../ai_approvals/data/ai_approvals_repository.dart';
import '../../ai_approvals/domain/ai_action_approval.dart';
import '../../appointments/data/appointments_repository.dart';
import '../../appointments/domain/appointment.dart';
import '../../settings/data/settings_repository.dart';
import '../../settings/domain/user_profile.dart';
import '../../tasks/data/tasks_repository.dart';
import '../../tasks/domain/task.dart';
import '../data/dashboard_repository.dart';
import '../domain/dashboard_models.dart';

/// Özet (home) tab. Stitch never designed a dedicated dashboard screen for
/// this project -- only a "Takvim" screen exists -- so this composes the
/// same bento/agenda visual language (see AppComponents) around the real,
/// thin DashboardSummary payload (4 counters, no server-side AI-brief
/// string) plus today's real appointments/tasks/approvals.
class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    final approvals = ref.watch(pendingAiApprovalsProvider);
    final tasks = ref.watch(tasksProvider);
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    final today = DateTime.now();
    final appointmentsAsync =
        ref.watch(appointmentsForMonthProvider(DateTime(today.year, today.month)));
    final todayTasks = _todayTasks(tasks.valueOrNull ?? const []);
    final todayAppointments = (appointmentsAsync.valueOrNull ?? const [])
        .where((appointment) => _isSameDay(appointment.startAt.toLocal(), today))
        .toList(growable: false)
      ..sort((a, b) => a.startAt.compareTo(b.startAt));

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(dashboardProvider.future),
        child: ListView(
          padding: kScreenPadding,
          children: [
            StitchScreenHeader(title: _greeting(currentUser)),
            dashboard.when(
              data: (data) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SectionHeading(
                    title: 'Bugünkü Program',
                    trailing: _formatHeaderDate(today),
                  ),
                  const SizedBox(height: 12),
                  if (todayAppointments.isEmpty)
                    _EmptyAgendaCard(onAdd: () => context.go('/app/appointments'))
                  else
                    ...todayAppointments.indexed.map(
                      (entry) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: _AgendaCard(
                          appointment: entry.$2,
                          accentIsPrimary: entry.$1.isOdd,
                        ),
                      ),
                    ),
                  const SizedBox(height: 20),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: BentoStatTile(
                          icon: Icons.task_alt,
                          label: 'Tamamlanan',
                          value:
                              '${todayTasks.where((task) => task.status == 'completed').length}/${todayTasks.length}',
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: InfoTile(
                          icon: Icons.forum,
                          label: 'AI Özeti',
                          text: _summaryText(data.summary),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  _AiSuggestionsSection(approvals: approvals.valueOrNull ?? const []),
                  const SizedBox(height: 24),
                  _TodayTasksSection(tasks: todayTasks),
                ],
              ),
              error: (error, stackTrace) => AppCard(
                child: Text(
                  readableApiError(error, 'Özet alınamadı. Bağlantıyı kontrol edip tekrar deneyin.'),
                ),
              ),
              loading: () => const Padding(
                padding: EdgeInsets.only(top: 60),
                child: Center(child: CircularProgressIndicator()),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

bool _isSameDay(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

List<Task> _todayTasks(List<Task> tasks) {
  final now = DateTime.now();
  final today = tasks.where((task) {
    final due = task.dueAt?.toLocal();
    return due != null && _isSameDay(due, now);
  }).toList(growable: false)
    ..sort((a, b) => (a.dueAt ?? now).compareTo(b.dueAt ?? now));
  return today;
}

String _greeting(CurrentUser? user) {
  final fullName = user?.profile?.fullName;
  final name = (fullName != null && fullName.trim().isNotEmpty)
      ? fullName.trim().split(RegExp(r'\s+')).first
      : (user?.email.contains('@') ?? false)
          ? user!.email.split('@').first
          : '';
  return name.isEmpty ? 'Günaydın' : 'Günaydın $name';
}

String _summaryText(DashboardSummary summary) {
  final parts = <String>[];
  if (summary.openTasksCount > 0) {
    parts.add('${summary.openTasksCount} açık görev');
  }
  if (summary.upcomingAppointmentsCount > 0) {
    parts.add('${summary.upcomingAppointmentsCount} yaklaşan randevu');
  }
  if (summary.pendingAiApprovalsCount > 0) {
    parts.add('${summary.pendingAiApprovalsCount} bekleyen AI önerisi');
  }
  if (parts.isEmpty) {
    return 'Bugün için bekleyen bir şey yok. Harika gidiyorsun!';
  }
  return 'Bugün ${parts.join(', ')} var.';
}

String _formatHeaderDate(DateTime value) {
  const months = [
    'Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz',
    'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara',
  ];
  return '${value.day} ${months[value.month - 1]}';
}

class _EmptyAgendaCard extends StatelessWidget {
  const _EmptyAgendaCard({required this.onAdd});

  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Icon(Icons.event_busy, color: theme.colorScheme.outline, size: 32),
          const SizedBox(height: 10),
          Text('Bugün için planlanmış bir şey yok', style: theme.textTheme.bodyMedium),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: onAdd,
            icon: const Icon(Icons.add),
            label: const Text('Randevu Ekle'),
          ),
        ],
      ),
    );
  }
}

class _AgendaCard extends StatelessWidget {
  const _AgendaCard({required this.appointment, required this.accentIsPrimary});

  final Appointment appointment;
  final bool accentIsPrimary;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accent =
        accentIsPrimary ? theme.colorScheme.primary : theme.colorScheme.secondary;

    return AppCard(
      child: Row(
        children: [
          Container(
            width: 4,
            height: 40,
            margin: const EdgeInsets.only(right: 14),
            decoration: BoxDecoration(
              color: accent,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
          SizedBox(
            width: 48,
            child: Text(
              _formatTime(appointment.startAt),
              style: theme.textTheme.titleMedium?.copyWith(
                color: accent,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          Container(width: 1, height: 32, color: theme.colorScheme.outlineVariant),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              appointment.title,
              style: theme.textTheme.titleMedium,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          IconButton.filledTonal(
            onPressed: () => context.go('/app/appointments'),
            icon: const Icon(Icons.link, size: 18),
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime value) {
    final local = value.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _AiSuggestionsSection extends StatelessWidget {
  const _AiSuggestionsSection({required this.approvals});

  final List<AiActionApproval> approvals;

  @override
  Widget build(BuildContext context) {
    if (approvals.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeading(
          title: 'Yapay Zeka Önerileri',
          trailing: 'Tümünü Gör',
          onTrailingTap: () => context.go('/app/calls'),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 150,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: approvals.length,
            separatorBuilder: (context, index) => const SizedBox(width: 12),
            itemBuilder: (context, index) => _SuggestionCard(approval: approvals[index]),
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
    return SizedBox(
      width: 260,
      child: AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TintedIcon(icon: Icons.auto_awesome, color: theme.colorScheme.primary, size: 34),
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
      ),
    );
  }

  Future<void> _approve() async {
    await _submit(() => ref.read(aiApprovalsRepositoryProvider).approve(widget.approval));
  }

  Future<void> _reject() async {
    await _submit(() => ref.read(aiApprovalsRepositoryProvider).reject(widget.approval.id));
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
      if (mounted) setState(() => _isSubmitting = false);
    }
  }
}

class _TodayTasksSection extends StatelessWidget {
  const _TodayTasksSection({required this.tasks});

  final List<Task> tasks;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Bugünün Görevleri', style: Theme.of(context).textTheme.titleMedium),
            IconButton(
              onPressed: () => context.go('/app/tasks'),
              icon: const Icon(Icons.add_circle, color: Color(0xFF3525CD)),
            ),
          ],
        ),
        if (tasks.isEmpty)
          const AppCard(
            child: Text('Görevler sekmesinden yeni bir görev ekleyebilirsin.'),
          )
        else
          ...tasks.map((task) => _TodayTaskTile(task: task)),
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

    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: AppCard(
        color: isCompleted ? const Color(0xFFF0EEFB) : Colors.white,
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
                    color: isCompleted ? theme.colorScheme.primary : const Color(0xFFC7C4D8),
                    width: 2,
                  ),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: isCompleted ? const Icon(Icons.check, size: 16, color: Colors.white) : null,
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
                      decoration: isCompleted ? TextDecoration.lineThrough : null,
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
      if (mounted) setState(() => _isSubmitting = false);
    }
  }
}

String _formatTime(DateTime value) {
  final local = value.toLocal();
  return '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
