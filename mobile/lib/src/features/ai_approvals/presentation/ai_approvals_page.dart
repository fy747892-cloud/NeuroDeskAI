import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../appointments/data/appointments_repository.dart';
import '../../deals/data/deals_repository.dart';
import '../../tasks/data/tasks_repository.dart';
import '../data/ai_approvals_repository.dart';
import '../domain/ai_action_approval.dart';

class AiApprovalsPage extends ConsumerWidget {
  const AiApprovalsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final approvals = ref.watch(pendingAiApprovalsProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(pendingAiApprovalsProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('AI Onay', style: theme.textTheme.headlineMedium),
          const SizedBox(height: 6),
          Text(
            'AI tarafından hazırlanan aksiyonları insan onayından geçir.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          approvals.when(
            data: (items) => items.isEmpty
                ? const _PageMessage(message: 'Bekleyen AI onayı yok.')
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _ApprovalsSummary(approvals: items),
                      const SizedBox(height: 14),
                      _BulkApprovalActions(approvals: items),
                      const SizedBox(height: 14),
                      ...items.map(
                        (approval) => _ApprovalCard(approval: approval),
                      ),
                    ],
                  ),
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'AI onayları alınamadı.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

class _BulkApprovalActions extends ConsumerStatefulWidget {
  const _BulkApprovalActions({required this.approvals});

  final List<AiActionApproval> approvals;

  @override
  ConsumerState<_BulkApprovalActions> createState() =>
      _BulkApprovalActionsState();
}

class _BulkApprovalActionsState extends ConsumerState<_BulkApprovalActions> {
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  Widget build(BuildContext context) {
    final tasks = widget.approvals.where(_isTask).toList(growable: false);
    final appointments =
        widget.approvals.where(_isAppointment).toList(growable: false);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Toplu işlem',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.tonalIcon(
                  onPressed: _isSubmitting || tasks.isEmpty
                      ? null
                      : () => _approveMany(tasks, 'Görevler oluşturuldu.'),
                  icon: const Icon(Icons.task_alt),
                  label: Text('Tüm görevleri onayla (${tasks.length})'),
                ),
                FilledButton.tonalIcon(
                  onPressed: _isSubmitting || appointments.isEmpty
                      ? null
                      : () => _approveMany(
                            appointments,
                            'Randevular oluşturuldu.',
                          ),
                  icon: const Icon(Icons.event_available),
                  label:
                      Text('Tüm randevuları onayla (${appointments.length})'),
                ),
                FilledButton.icon(
                  onPressed: _isSubmitting
                      ? null
                      : () => _approveMany(
                            widget.approvals,
                            'Bekleyen öneriler onaylandı.',
                          ),
                  icon: const Icon(Icons.done_all),
                  label: const Text('Hepsini onayla'),
                ),
              ],
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                _errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _approveMany(
    List<AiActionApproval> approvals,
    String successMessage,
  ) async {
    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });
    try {
      await ref.read(aiApprovalsRepositoryProvider).approveMany(approvals);
      ref.invalidate(pendingAiApprovalsProvider);
      ref.invalidate(tasksProvider);
      ref.invalidate(appointmentsProvider);
      ref.invalidate(dealsProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(successMessage),
          duration: const Duration(seconds: 2),
        ),
      );
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Toplu işlem tamamlanamadı.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}

bool _isTask(AiActionApproval approval) {
  return approval.actionType == 'task' ||
      approval.actionType == 'create_task' ||
      approval.actionType == 'task/create_task';
}

bool _isAppointment(AiActionApproval approval) {
  return approval.actionType == 'appointment' ||
      approval.actionType == 'create_appointment' ||
      approval.actionType == 'appointment/create_appointment';
}

class _ApprovalsSummary extends StatelessWidget {
  const _ApprovalsSummary({required this.approvals});

  final List<AiActionApproval> approvals;

  @override
  Widget build(BuildContext context) {
    final appointmentCount = approvals.where(_isAppointment).length;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF17152F),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: _SummaryMetric(
              label: 'Bekleyen',
              value: approvals.length.toString(),
              icon: Icons.verified_outlined,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Takvim önerisi',
              value: appointmentCount.toString(),
              icon: Icons.event_available,
            ),
          ),
        ],
      ),
    );
  }
}

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 38,
          height: 38,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: Colors.white, size: 20),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
              ),
              Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white.withValues(alpha: 0.72),
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ApprovalCard extends ConsumerStatefulWidget {
  const _ApprovalCard({required this.approval});

  final AiActionApproval approval;

  @override
  ConsumerState<_ApprovalCard> createState() => _ApprovalCardState();
}

class _ApprovalCardState extends ConsumerState<_ApprovalCard> {
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  Widget build(BuildContext context) {
    final approval = widget.approval;
    final confidence = approval.confidenceScore == null
        ? null
        : '${(approval.confidenceScore! * 100).round()}%';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: const Color(0x1A3525CD),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.auto_awesome,
                    color: Color(0xFF3525CD),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    approval.displayTitle,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Chip(label: Text(approval.actionLabel)),
              ],
            ),
            const SizedBox(height: 10),
            Text(approval.displayDescription),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFF4F5FB),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Neden önerildi?',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    approval.reasonText,
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 12,
              runSpacing: 6,
              children: [
                _MetaLine(
                  icon: Icons.hub_outlined,
                  text: 'Kaynak: ${approval.sourceType}',
                ),
                if (confidence != null)
                  _MetaLine(
                    icon: Icons.speed,
                    text: 'Güven: $confidence',
                  ),
                if (approval.expiresAt != null)
                  _MetaLine(
                    icon: Icons.timer_outlined,
                    text: 'Son: ${_formatDate(approval.expiresAt!)}',
                  ),
              ],
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 10),
              Text(
                _errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _isSubmitting ? null : () => _reject(approval),
                    icon: const Icon(Icons.close),
                    label: Text(_isSubmitting ? 'Bekle' : 'Reddet'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _isSubmitting ? null : () => _approve(approval),
                    icon: const Icon(Icons.check),
                    label: Text(_isSubmitting ? 'İşleniyor' : 'Onayla'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _approve(AiActionApproval approval) async {
    await _submit(
      () => ref.read(aiApprovalsRepositoryProvider).approve(approval),
      approval,
    );
  }

  Future<void> _reject(AiActionApproval approval) async {
    await _submit(
      () => ref.read(aiApprovalsRepositoryProvider).reject(approval.id),
      null,
    );
  }

  Future<void> _submit(
    Future<Object?> Function() action,
    AiActionApproval? approvedAction,
  ) async {
    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });
    try {
      await action();
      ref.invalidate(pendingAiApprovalsProvider);
      if (approvedAction != null && mounted) {
        _invalidateTargetList(approvedAction);
        final route = _routeFor(approvedAction);
        final messenger = ScaffoldMessenger.of(context);
        messenger.hideCurrentSnackBar();
        if (route != null) {
          context.go(route);
        }
        messenger.showSnackBar(
          SnackBar(
            content: Text('${approvedAction.actionLabel} oluşturuldu.'),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'İşlem tamamlanamadı.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  void _invalidateTargetList(AiActionApproval approval) {
    switch (approval.actionType) {
      case 'task':
      case 'create_task':
      case 'task/create_task':
        ref.invalidate(tasksProvider);
      case 'appointment':
      case 'create_appointment':
      case 'appointment/create_appointment':
        ref.invalidate(appointmentsProvider);
      case 'deal':
      case 'create_deal':
      case 'deal/create_deal':
        ref.invalidate(dealsProvider);
    }
  }

  String? _routeFor(AiActionApproval approval) {
    return switch (approval.actionType) {
      'task' || 'create_task' || 'task/create_task' => '/app/tasks',
      'appointment' ||
      'create_appointment' ||
      'appointment/create_appointment' =>
        '/app/appointments',
      'deal' || 'create_deal' || 'deal/create_deal' => '/app/deals',
      _ => null,
    };
  }

  String _formatDate(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}.'
        '${local.month.toString().padLeft(2, '0')} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _MetaLine extends StatelessWidget {
  const _MetaLine({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          size: 16,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 6),
        Text(text, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(message),
      ),
    );
  }
}
