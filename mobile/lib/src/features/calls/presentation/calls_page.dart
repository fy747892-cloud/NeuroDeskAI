import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../../conversations/data/conversations_repository.dart';
import '../data/calls_repository.dart';
import '../domain/call_record.dart';

class CallsPage extends ConsumerStatefulWidget {
  const CallsPage({super.key});

  @override
  ConsumerState<CallsPage> createState() => _CallsPageState();
}

class _CallsPageState extends ConsumerState<CallsPage> {
  String? _notice;

  @override
  Widget build(BuildContext context) {
    final calls = ref.watch(callsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(callsProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Cagrilar', style: theme.textTheme.headlineMedium),
            const SizedBox(height: 6),
            Text(
              'Telefon kaydi otomatik alinmaz; gorusme metnini bilincli olarak ekle.',
              style: theme.textTheme.bodyMedium,
            ),
            if (_notice != null) ...[
              const SizedBox(height: 12),
              _PageMessage(message: _notice!),
            ],
            const SizedBox(height: 16),
            calls.when(
              data: (items) => items.isEmpty
                  ? const _PageMessage(message: 'Henuz cagri kaydi yok.')
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _CallsSummary(calls: items),
                        const SizedBox(height: 14),
                        ...items.map((call) => _CallCard(call: call)),
                      ],
                    ),
              error: (error, stackTrace) => _PageMessage(
                message: readableApiError(error, 'Cagrilar alinamadi.'),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Cagri metni ekle',
        onPressed: _showCreateSheet,
        child: const Icon(Icons.add_call),
      ),
    );
  }

  Future<void> _showCreateSheet() async {
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => const _CreateCallSheet(),
    );
    if (saved == true) {
      setState(() => _notice = 'Cagri kaydedildi ve AI analiz baslatildi.');
      ref.invalidate(callsProvider);
      ref.invalidate(conversationsProvider);
    }
  }
}

class _CallsSummary extends StatelessWidget {
  const _CallsSummary({required this.calls});

  final List<CallRecord> calls;

  @override
  Widget build(BuildContext context) {
    final withTranscript =
        calls.where((call) => call.transcriptions.isNotEmpty).length;

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
              label: 'Cagri',
              value: calls.length.toString(),
              icon: Icons.call_outlined,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Transkript',
              value: withTranscript.toString(),
              icon: Icons.notes_outlined,
            ),
          ),
        ],
      ),
    );
  }
}

class _CallCard extends StatelessWidget {
  const _CallCard({required this.call});

  final CallRecord call;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final firstTranscript =
        call.transcriptions.isEmpty ? null : call.transcriptions.first;

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
                  child: const Icon(Icons.call, color: Color(0xFF3525CD)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    call.phoneNumber?.isNotEmpty == true
                        ? call.phoneNumber!
                        : 'Manuel cagri',
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                _StatusChip(status: call.status),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 6,
              children: [
                _MetaLine(
                  icon: Icons.swap_calls,
                  text: _directionLabel(call.callDirection),
                ),
                _MetaLine(
                  icon: Icons.schedule,
                  text: _formatDateTime(call.startedAt ?? call.createdAt),
                ),
                if (call.durationSeconds != null)
                  _MetaLine(
                    icon: Icons.timer_outlined,
                    text: _formatDuration(call.durationSeconds!),
                  ),
              ],
            ),
            if (firstTranscript != null) ...[
              const SizedBox(height: 10),
              Text(
                firstTranscript.transcriptText,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodyMedium,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _CreateCallSheet extends ConsumerStatefulWidget {
  const _CreateCallSheet();

  @override
  ConsumerState<_CreateCallSheet> createState() => _CreateCallSheetState();
}

class _CreateCallSheetState extends ConsumerState<_CreateCallSheet> {
  final _titleController = TextEditingController();
  final _participantsController = TextEditingController();
  final _phoneController = TextEditingController();
  final _transcriptController = TextEditingController();
  String _direction = 'outbound';
  bool _isSaving = false;
  String? _errorMessage;

  @override
  void dispose() {
    _titleController.dispose();
    _participantsController.dispose();
    _phoneController.dispose();
    _transcriptController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.viewInsetsOf(context).bottom;

    return Padding(
      padding: EdgeInsets.fromLTRB(16, 16, 16, 16 + bottomInset),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Cagri metni ekle',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 14),
            TextField(
              controller: _titleController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Baslik',
                prefixIcon: Icon(Icons.title),
              ),
            ),
            const SizedBox(height: 10),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'outbound', label: Text('Giden')),
                ButtonSegment(value: 'inbound', label: Text('Gelen')),
              ],
              selected: {_direction},
              onSelectionChanged: (values) {
                setState(() => _direction = values.first);
              },
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _phoneController,
              keyboardType: TextInputType.phone,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Telefon',
                prefixIcon: Icon(Icons.phone_outlined),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _participantsController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Katilimcilar',
                hintText: 'Virgul ile ayir',
                prefixIcon: Icon(Icons.people_alt_outlined),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _transcriptController,
              minLines: 5,
              maxLines: 8,
              decoration: const InputDecoration(
                labelText: 'Transkript',
                prefixIcon: Icon(Icons.notes_outlined),
              ),
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 10),
              Text(
                _errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 14),
            FilledButton.icon(
              onPressed: _isSaving ? null : _save,
              icon: _isSaving
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.auto_awesome),
              label: const Text('Kaydet ve analiz et'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _save() async {
    final title = _titleController.text.trim();
    final transcript = _transcriptController.text.trim();
    final participants = _participantsController.text
        .split(',')
        .map((name) => name.trim())
        .where((name) => name.isNotEmpty)
        .toList(growable: false);

    if (title.isEmpty || transcript.isEmpty) {
      setState(() => _errorMessage = 'Baslik ve transkript zorunlu.');
      return;
    }

    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });

    try {
      final result = await ref.read(callsRepositoryProvider).createFromText(
            title: title,
            transcriptText: transcript,
            participantNames: participants,
            callDirection: _direction,
            phoneNumber: _phoneController.text,
          );
      await ref
          .read(callsRepositoryProvider)
          .requestAnalysis(result.conversationId);
      if (mounted) {
        Navigator.of(context).pop(true);
      }
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Cagri kaydedilemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
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
        const SizedBox(width: 5),
        Text(text, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final label = switch (status.toLowerCase()) {
      'uploaded' => 'Yuklendi',
      'processed' => 'Islendi',
      'failed' => 'Hata',
      _ => status,
    };

    return Chip(label: Text(label), visualDensity: VisualDensity.compact);
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

String _directionLabel(String? value) {
  return switch (value) {
    'inbound' => 'Gelen',
    'outbound' => 'Giden',
    _ => 'Yok',
  };
}

String _formatDuration(int seconds) {
  final minutes = seconds ~/ 60;
  final remaining = seconds % 60;
  return '${minutes}d ${remaining}s';
}

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
