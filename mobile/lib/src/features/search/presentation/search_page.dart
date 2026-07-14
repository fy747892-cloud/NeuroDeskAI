import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../data/search_repository.dart';
import '../domain/search_result.dart';

class SearchPage extends ConsumerStatefulWidget {
  const SearchPage({super.key});

  @override
  ConsumerState<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends ConsumerState<SearchPage> {
  final _queryController = TextEditingController();
  int _limit = 10;
  bool _isSearching = false;
  String? _errorMessage;
  List<SearchResult> _results = const [];

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Arama', style: theme.textTheme.headlineMedium),
        const SizedBox(height: 6),
        Text(
          'Gorev, randevu, gorusme ve kisiler arasinda anlamsal arama yap.',
          style: theme.textTheme.bodyMedium,
        ),
        const SizedBox(height: 16),
        _SearchForm(
          controller: _queryController,
          limit: _limit,
          isSearching: _isSearching,
          onLimitChanged: (value) => setState(() => _limit = value),
          onSubmit: _search,
        ),
        if (_errorMessage != null) ...[
          const SizedBox(height: 12),
          _PageMessage(message: _errorMessage!),
        ],
        const SizedBox(height: 16),
        _SearchSummary(results: _results),
        const SizedBox(height: 14),
        if (_results.isEmpty)
          const _EmptySearch()
        else
          ..._results.map((result) => _ResultCard(result: result)),
      ],
    );
  }

  Future<void> _search() async {
    final query = _queryController.text.trim();
    if (query.isEmpty || _isSearching) {
      return;
    }

    setState(() {
      _isSearching = true;
      _errorMessage = null;
    });

    try {
      final results = await ref.read(searchRepositoryProvider).semanticSearch(
            query: query,
            limit: _limit,
          );
      setState(() => _results = results);
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Arama tamamlanamadi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSearching = false);
      }
    }
  }
}

class _SearchForm extends StatelessWidget {
  const _SearchForm({
    required this.controller,
    required this.limit,
    required this.isSearching,
    required this.onLimitChanged,
    required this.onSubmit,
  });

  final TextEditingController controller;
  final int limit;
  final bool isSearching;
  final ValueChanged<int> onLimitChanged;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: [
            TextField(
              controller: controller,
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => onSubmit(),
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.travel_explore),
                labelText: 'Sorgu',
                hintText: 'Geciken takipler',
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: SegmentedButton<int>(
                    segments: const [
                      ButtonSegment(value: 5, label: Text('5')),
                      ButtonSegment(value: 10, label: Text('10')),
                      ButtonSegment(value: 20, label: Text('20')),
                    ],
                    selected: {limit},
                    onSelectionChanged: (values) {
                      onLimitChanged(values.first);
                    },
                  ),
                ),
                const SizedBox(width: 10),
                IconButton.filled(
                  tooltip: 'Ara',
                  onPressed: isSearching ? null : onSubmit,
                  icon: isSearching
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.search),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SearchSummary extends StatelessWidget {
  const _SearchSummary({required this.results});

  final List<SearchResult> results;

  @override
  Widget build(BuildContext context) {
    final taskCount =
        results.where((result) => result.sourceType == 'task').length;
    final contactCount =
        results.where((result) => result.sourceType == 'contact').length;

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
              label: 'Sonuc',
              value: results.length.toString(),
              icon: Icons.search,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Gorev/Kisi',
              value: '${taskCount + contactCount}',
              icon: Icons.hub_outlined,
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

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});

  final SearchResult result;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _SourceIcon(sourceType: result.sourceType),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    result.title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Chip(
                  label: Text('${(result.score * 100).round()}'),
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(result.snippet, style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 8),
            Text(
              _sourceLabel(result.sourceType),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  String _sourceLabel(String value) {
    return switch (value) {
      'task' => 'Gorev',
      'appointment' => 'Randevu',
      'conversation' => 'Gorusme',
      'contact' => 'Kisi',
      'email' => 'E-posta',
      _ => value,
    };
  }
}

class _SourceIcon extends StatelessWidget {
  const _SourceIcon({required this.sourceType});

  final String sourceType;

  @override
  Widget build(BuildContext context) {
    final icon = switch (sourceType) {
      'task' => Icons.checklist,
      'appointment' => Icons.event,
      'conversation' => Icons.forum,
      'contact' => Icons.person,
      'email' => Icons.mail,
      _ => Icons.search,
    };

    return Container(
      width: 38,
      height: 38,
      decoration: BoxDecoration(
        color: const Color(0x1A3525CD),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: const Color(0xFF3525CD), size: 20),
    );
  }
}

class _EmptySearch extends StatelessWidget {
  const _EmptySearch();

  @override
  Widget build(BuildContext context) {
    return const _PageMessage(
      message: 'Arama sonucu yok. Bir sorgu yazip aramayi baslat.',
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
