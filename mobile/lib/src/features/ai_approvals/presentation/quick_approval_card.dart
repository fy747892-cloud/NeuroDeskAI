import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../data/ai_approvals_repository.dart';
import '../domain/ai_action_approval.dart';

class QuickApprovalCard extends ConsumerStatefulWidget {
  const QuickApprovalCard({
    super.key,
    required this.approvals,
    this.onChanged,
  });

  final List<AiActionApproval> approvals;
  final VoidCallback? onChanged;

  @override
  ConsumerState<QuickApprovalCard> createState() => _QuickApprovalCardState();
}

class _QuickApprovalCardState extends ConsumerState<QuickApprovalCard> {
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  Widget build(BuildContext context) {
    if (widget.approvals.isEmpty) {
      return const SizedBox.shrink();
    }

    final theme = Theme.of(context);
    final first = widget.approvals.first;
    final extraCount = widget.approvals.length - 1;

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.primary.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: theme.colorScheme.primary.withValues(alpha: 0.18),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.bolt, size: 18, color: theme.colorScheme.primary),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  '${widget.approvals.length} öneri hazır',
                  style: theme.textTheme.labelLarge?.copyWith(
                    color: theme.colorScheme.primary,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              TextButton(
                onPressed: _isSubmitting ? null : () => context.go('/app/approvals'),
                child: const Text('Onay Merkezi'),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            first.displayTitle,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.titleSmall,
          ),
          const SizedBox(height: 3),
          Text(
            extraCount > 0
                ? '${first.displayDescription} + $extraCount öneri daha'
                : first.displayDescription,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.bodySmall,
          ),
          if (_errorMessage != null) ...[
            const SizedBox(height: 6),
            Text(
              _errorMessage!,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.error,
              ),
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _isSubmitting ? null : _rejectFirst,
                  icon: const Icon(Icons.close, size: 18),
                  label: const Text('Reddet'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _isSubmitting ? null : () => _editAndApprove(first),
                  icon: const Icon(Icons.edit_outlined, size: 18),
                  label: const Text('Düzenle'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: FilledButton.icon(
                  onPressed: _isSubmitting ? null : _approveFirst,
                  icon: const Icon(Icons.check, size: 18),
                  label: const Text('Onayla'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _approveFirst() async {
    await _submit(
      () => ref.read(aiApprovalsRepositoryProvider).approve(widget.approvals.first),
    );
  }

  Future<void> _rejectFirst() async {
    await _submit(
      () => ref
          .read(aiApprovalsRepositoryProvider)
          .reject(widget.approvals.first.id),
    );
  }

  Future<void> _editAndApprove(AiActionApproval approval) async {
    final titleController = TextEditingController(
      text: (approval.suggestedPayload['title'] ??
              approval.suggestedPayload['subject'] ??
              approval.displayTitle)
          .toString(),
    );
    final descriptionController = TextEditingController(
      text: (approval.suggestedPayload['description'] ??
              approval.suggestedPayload['notes'] ??
              approval.displayDescription)
          .toString(),
    );

    final editedPayload = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Öneriyi düzenle'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleController,
                decoration: const InputDecoration(labelText: 'Başlık'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: descriptionController,
                minLines: 3,
                maxLines: 5,
                decoration: const InputDecoration(labelText: 'Açıklama'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Vazgeç'),
          ),
          FilledButton(
            onPressed: () {
              final payload = Map<String, dynamic>.from(
                approval.suggestedPayload,
              );
              payload['title'] = titleController.text.trim();
              payload['description'] = descriptionController.text.trim();
              Navigator.of(context).pop(payload);
            },
            child: const Text('Kaydet ve onayla'),
          ),
        ],
      ),
    );

    titleController.dispose();
    descriptionController.dispose();

    if (editedPayload == null) {
      return;
    }

    await _submit(
      () => ref.read(aiApprovalsRepositoryProvider).approve(
            approval,
            approvedPayload: editedPayload,
          ),
    );
  }

  Future<void> _submit(Future<Object?> Function() action) async {
    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });
    try {
      await action();
      ref.invalidate(pendingAiApprovalsProvider);
      widget.onChanged?.call();
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
}
