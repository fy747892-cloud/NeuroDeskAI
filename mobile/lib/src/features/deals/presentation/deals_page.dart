import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
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

    return Scaffold(
      body: RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        padding: kScreenPadding,
        children: [
          const StitchScreenHeader(title: 'Fırsatlar'),
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
                  _StageFilter(
                    selectedStage: _selectedStage,
                    deals: items,
                    onChanged: (stage) {
                      setState(() => _selectedStage = stage);
                    },
                  ),
                  const SizedBox(height: 16),
                  if (visible.isEmpty)
                    const _PageMessage(message: 'Bu aşamada fırsat yok.')
                  else
                    for (var i = 0; i < visible.length; i++)
                      _DealCard(
                        deal: visible[i],
                        contact: contactMap[visible[i].contactId],
                        isUpdating: _activeDealId == visible[i].id,
                        colorIndex: i,
                        onStageChanged: (stage) => _updateStage(visible[i], stage),
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
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Fırsat ekle',
        onPressed: () => _showCreateDialog(context),
        child: const Icon(Icons.add),
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
    return SizedBox(
      height: 40,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          _StageTab(
            label: 'Tüm',
            selected: selectedStage == 'all',
            onSelected: () => onChanged('all'),
          ),
          for (final stage in dealStages)
            _StageTab(
              label: dealStageLabel(stage),
              selected: selectedStage == stage,
              onSelected: () => onChanged(stage),
            ),
        ],
      ),
    );
  }
}

class _StageTab extends StatelessWidget {
  const _StageTab({
    required this.label,
    required this.selected,
    required this.onSelected,
  });

  final String label;
  final bool selected;
  final VoidCallback onSelected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(right: 24),
      child: InkWell(
        onTap: onSelected,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              label,
              style: TextStyle(
                color: selected ? theme.colorScheme.secondary : theme.colorScheme.onSurfaceVariant,
                fontWeight: selected ? FontWeight.w800 : FontWeight.normal,
              ),
            ),
            const SizedBox(height: 6),
            Container(
              height: 3,
              width: 32,
              decoration: BoxDecoration(
                color: selected ? theme.colorScheme.secondary : Colors.transparent,
                borderRadius: BorderRadius.circular(999),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Cycling icon/color pairs, matching the same decorative palette used in the
// Daha Fazla module grid -- purely visual variety, not tied to deal data.
const _dealAccents = [
  (Color(0xFF059669), Icons.business_outlined),
  (Color(0xFF4F46E5), Icons.rocket_launch_outlined),
  (Color(0xFFD97706), Icons.bolt_outlined),
  (Color(0xFF7C3AED), Icons.palette_outlined),
  (Color(0xFFE11D48), Icons.storefront_outlined),
  (Color(0xFF0891B2), Icons.apartment_outlined),
];

class _DealCard extends StatelessWidget {
  const _DealCard({
    required this.deal,
    required this.isUpdating,
    required this.onStageChanged,
    required this.colorIndex,
    this.contact,
  });

  final Deal deal;
  final Contact? contact;
  final bool isUpdating;
  final int colorIndex;
  final ValueChanged<String> onStageChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (accentColor, accentIcon) =
        _dealAccents[colorIndex % _dealAccents.length];

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: accentColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(accentIcon, color: Colors.white, size: 20),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(deal.title, style: theme.textTheme.titleMedium),
                    if (contact != null)
                      Text(
                        [
                          contact!.fullName,
                          if (contact!.company != null) contact!.company!,
                        ].join(' - '),
                        style: theme.textTheme.bodySmall,
                      ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _StageBadge(
                deal: deal,
                isUpdating: isUpdating,
                onStageChanged: onStageChanged,
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Tutar', style: theme.textTheme.bodySmall),
                    Text(
                      '${_formatNumber(deal.value ?? 0)} ${deal.currency}',
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: theme.colorScheme.secondary,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
              if (deal.expectedCloseDate != null)
                Row(
                  children: [
                    Icon(Icons.schedule,
                        size: 16, color: theme.colorScheme.outline),
                    const SizedBox(width: 4),
                    Text(_formatDate(deal.expectedCloseDate!),
                        style: theme.textTheme.bodySmall),
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

class _StageBadge extends StatelessWidget {
  const _StageBadge({
    required this.deal,
    required this.isUpdating,
    required this.onStageChanged,
  });

  final Deal deal;
  final bool isUpdating;
  final ValueChanged<String> onStageChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (isUpdating) {
      return const SizedBox(
        width: 16,
        height: 16,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    }
    return PopupMenuButton<String>(
      tooltip: 'Aşamayı değiştir',
      onSelected: onStageChanged,
      itemBuilder: (context) => [
        for (final stage in dealStages)
          PopupMenuItem(value: stage, child: Text(dealStageLabel(stage))),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: theme.colorScheme.primary.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          dealStages.contains(deal.stage)
              ? dealStageLabel(deal.stage)
              : deal.stage,
          style: TextStyle(
            color: theme.colorScheme.primary,
            fontWeight: FontWeight.w700,
            fontSize: 12,
          ),
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
                  labelText: 'Değer',
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
                  decoration: const InputDecoration(labelText: 'İlgili kişi'),
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
                label: const Text('Oluştur'),
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

class _PageMessage extends StatelessWidget {
  const _PageMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return AppCard(child: Text(message));
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
