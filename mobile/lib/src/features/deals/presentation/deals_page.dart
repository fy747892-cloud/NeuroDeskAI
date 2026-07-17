import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../../contacts/data/contacts_repository.dart';
import '../../contacts/domain/contact.dart';
import '../data/deals_repository.dart';
import '../domain/deal.dart';

class DealsPage extends ConsumerStatefulWidget {
  const DealsPage({super.key});

  @override
  ConsumerState<DealsPage> createState() => _DealsPageState();
}

class _DealsPageState extends ConsumerState<DealsPage> {
  String _selectedStage = 'all';
  String? _activeDealId;

  @override
  Widget build(BuildContext context) {
    final deals = ref.watch(dealsProvider);
    final contacts = ref.watch(contactsProvider(null));
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Fırsatlar', style: theme.textTheme.headlineMedium),
                    const SizedBox(height: 6),
                    Text(
                      'Pipeline değerini ve aşama hareketlerini takip et.',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              FilledButton.icon(
                onPressed: () => _showCreateDialog(context),
                icon: const Icon(Icons.add),
                label: const Text('Yeni'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          deals.when(
            data: (items) {
              final contactMap = contacts.valueOrNull == null
                  ? const <String, Contact>{}
                  : {
                      for (final contact in contacts.valueOrNull!)
                        contact.id: contact,
                    };
              final visible = _selectedStage == 'all'
                  ? items
                  : items
                      .where((deal) => deal.stage == _selectedStage)
                      .toList(growable: false);

              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _PipelineSummary(deals: items),
                  const SizedBox(height: 14),
                  _StageFilter(
                    selectedStage: _selectedStage,
                    deals: items,
                    onChanged: (stage) {
                      setState(() => _selectedStage = stage);
                    },
                  ),
                  const SizedBox(height: 14),
                  if (visible.isEmpty)
                    const _PageMessage(message: 'Bu aşamada fırsat yok.')
                  else
                    ...visible.map(
                      (deal) => _DealCard(
                        deal: deal,
                        contact: contactMap[deal.contactId],
                        isUpdating: _activeDealId == deal.id,
                        onStageChanged: (stage) => _updateStage(deal, stage),
                      ),
                    ),
                ],
              );
            },
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'Fırsatlar alınamadı.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }

  Future<void> _refresh() async {
    ref.invalidate(dealsProvider);
    ref.invalidate(contactsProvider(null));
    await ref.read(dealsProvider.future);
  }

  Future<void> _updateStage(Deal deal, String stage) async {
    if (stage == deal.stage || _activeDealId != null) {
      return;
    }

    setState(() => _activeDealId = deal.id);
    try {
      await ref.read(dealsRepositoryProvider).updateStage(deal.id, stage);
      ref.invalidate(dealsProvider);
      await ref.read(dealsProvider.future);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text(readableApiError(error, 'Aşama güncellenemedi.'))),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _activeDealId = null);
      }
    }
  }

  Future<void> _showCreateDialog(BuildContext context) async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (context) => const _CreateDealSheet(),
    );
    if (created == true) {
      ref.invalidate(dealsProvider);
      await ref.read(dealsProvider.future);
    }
  }
}

class _PipelineSummary extends StatelessWidget {
  const _PipelineSummary({required this.deals});

  final List<Deal> deals;

  @override
  Widget build(BuildContext context) {
    final openDeals = deals
        .where((deal) => openDealStages.contains(deal.stage))
        .toList(growable: false);
    final totalValue = openDeals.fold<double>(
      0,
      (sum, deal) => sum + (deal.value ?? 0),
    );
    final currency = openDeals.isEmpty ? 'TRY' : openDeals.first.currency;

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
              label: 'Açık',
              value: openDeals.length.toString(),
              icon: Icons.account_tree_outlined,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: currency,
              value: _formatNumber(totalValue),
              icon: Icons.payments_outlined,
            ),
          ),
        ],
      ),
    );
  }
}

class _StageFilter extends StatelessWidget {
  const _StageFilter({
    required this.selectedStage,
    required this.deals,
    required this.onChanged,
  });

  final String selectedStage;
  final List<Deal> deals;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          _StageChip(
            label: 'Tum',
            count: deals.length,
            selected: selectedStage == 'all',
            onSelected: () => onChanged('all'),
          ),
          for (final stage in dealStages)
            _StageChip(
              label: dealStageLabel(stage),
              count: deals.where((deal) => deal.stage == stage).length,
              selected: selectedStage == stage,
              onSelected: () => onChanged(stage),
            ),
        ],
      ),
    );
  }
}

class _StageChip extends StatelessWidget {
  const _StageChip({
    required this.label,
    required this.count,
    required this.selected,
    required this.onSelected,
  });

  final String label;
  final int count;
  final bool selected;
  final VoidCallback onSelected;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text('$label $count'),
        selected: selected,
        onSelected: (_) => onSelected(),
      ),
    );
  }
}

class _DealCard extends StatelessWidget {
  const _DealCard({
    required this.deal,
    required this.isUpdating,
    required this.onStageChanged,
    this.contact,
  });

  final Deal deal;
  final Contact? contact;
  final bool isUpdating;
  final ValueChanged<String> onStageChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isAiSourced = deal.sourceType != 'manual';

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
                Expanded(
                  child: Text(deal.title, style: theme.textTheme.titleMedium),
                ),
                Chip(
                  label: Text(isAiSourced ? 'AI' : 'Manuel'),
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
            if (contact != null) ...[
              const SizedBox(height: 8),
              _MetaLine(
                icon: Icons.person_outline,
                text: [
                  contact!.fullName,
                  if (contact!.company != null) contact!.company!,
                ].join(' - '),
              ),
            ],
            if (deal.expectedCloseDate != null) ...[
              const SizedBox(height: 8),
              _MetaLine(
                icon: Icons.event_outlined,
                text: 'Kapanış: ${_formatDate(deal.expectedCloseDate!)}',
              ),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Text(
                    '${_formatNumber(deal.value ?? 0)} ${deal.currency}',
                    style: theme.textTheme.titleLarge?.copyWith(
                      color: const Color(0xFF3525CD),
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                DropdownButton<String>(
                  value: deal.stage,
                  onChanged: isUpdating || !dealStages.contains(deal.stage)
                      ? null
                      : (stage) {
                          if (stage != null) {
                            onStageChanged(stage);
                          }
                        },
                  items: [
                    for (final stage in dealStages)
                      DropdownMenuItem(
                        value: stage,
                        child: Text(dealStageLabel(stage)),
                      ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _CreateDealSheet extends ConsumerStatefulWidget {
  const _CreateDealSheet();

  @override
  ConsumerState<_CreateDealSheet> createState() => _CreateDealSheetState();
}

class _CreateDealSheetState extends ConsumerState<_CreateDealSheet> {
  final _titleController = TextEditingController();
  final _valueController = TextEditingController();
  String _currency = 'TRY';
  String? _contactId;
  DateTime? _expectedCloseDate;
  bool _isSaving = false;
  String? _errorMessage;

  @override
  void dispose() {
    _titleController.dispose();
    _valueController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final contacts = ref.watch(contactsProvider(null));

    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: 16,
          right: 16,
          top: 16,
          bottom: MediaQuery.viewInsetsOf(context).bottom + 16,
        ),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Yeni fırsat',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 14),
              TextField(
                controller: _titleController,
                decoration: const InputDecoration(
                  labelText: 'Başlık',
                  prefixIcon: Icon(Icons.sell_outlined),
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _valueController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Deger',
                  prefixIcon: Icon(Icons.payments_outlined),
                ),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                initialValue: _currency,
                decoration: const InputDecoration(labelText: 'Para birimi'),
                items: const [
                  DropdownMenuItem(value: 'TRY', child: Text('TRY')),
                  DropdownMenuItem(value: 'USD', child: Text('USD')),
                  DropdownMenuItem(value: 'EUR', child: Text('EUR')),
                ],
                onChanged: (value) =>
                    setState(() => _currency = value ?? 'TRY'),
              ),
              const SizedBox(height: 10),
              contacts.when(
                data: (items) => DropdownButtonFormField<String>(
                  initialValue: _contactId,
                  decoration: const InputDecoration(labelText: 'Ilgili kisi'),
                  items: [
                    const DropdownMenuItem(
                        value: null, child: Text('Seçilmedi')),
                    for (final contact in items)
                      DropdownMenuItem(
                        value: contact.id,
                        child: Text(contact.fullName),
                      ),
                  ],
                  onChanged: (value) => setState(() => _contactId = value),
                ),
                error: (error, stackTrace) =>
                    const _PageMessage(message: 'Kişiler alınamadı.'),
                loading: () => const LinearProgressIndicator(),
              ),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: _pickDate,
                icon: const Icon(Icons.event_outlined),
                label: Text(
                  _expectedCloseDate == null
                      ? 'Kapanış tarihi seç'
                      : _formatDate(_expectedCloseDate!),
                ),
              ),
              if (_errorMessage != null) ...[
                const SizedBox(height: 10),
                _PageMessage(message: _errorMessage!),
              ],
              const SizedBox(height: 14),
              FilledButton.icon(
                onPressed: _isSaving ? null : _save,
                icon: _isSaving
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.check),
                label: const Text('Olustur'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      firstDate: DateTime(now.year, now.month, now.day),
      lastDate: DateTime(now.year + 3),
      initialDate: _expectedCloseDate ?? now,
    );
    if (picked != null) {
      setState(() => _expectedCloseDate = picked);
    }
  }

  Future<void> _save() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      setState(() => _errorMessage = 'Başlık zorunlu.');
      return;
    }

    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });

    try {
      await ref.read(dealsRepositoryProvider).createDeal(
            title: title,
            value: _valueController.text,
            currency: _currency,
            contactId: _contactId,
            expectedCloseDate: _expectedCloseDate,
          );
      if (mounted) {
        Navigator.of(context).pop(true);
      }
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Fırsat oluşturulamadı.');
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
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
              ),
              Text(
                label,
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
      children: [
        Icon(
          icon,
          size: 16,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 6),
        Expanded(
          child: Text(text, style: Theme.of(context).textTheme.bodySmall),
        ),
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

String _formatDate(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')}.${local.year}';
}

String _formatNumber(double value) {
  final text = value.toStringAsFixed(value.truncateToDouble() == value ? 0 : 2);
  return text.replaceAllMapped(
    RegExp(r'\B(?=(\d{3})+(?!\d))'),
    (match) => '.',
  );
}
