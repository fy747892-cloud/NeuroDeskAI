import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
import '../data/analytics_repository.dart';
import '../domain/analytics_models.dart';

class AnalyticsPage extends ConsumerStatefulWidget {
  const AnalyticsPage({super.key});

  @override
  ConsumerState<AnalyticsPage> createState() => _AnalyticsPageState();
}

class _AnalyticsPageState extends ConsumerState<AnalyticsPage> {
  bool _isAggregating = false;

  @override
  Widget build(BuildContext context) {
    final snapshot = ref.watch(analyticsSnapshotProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(analyticsSnapshotProvider.future),
      child: ListView(
        padding: kScreenPadding,
        children: [
          StitchDetailHeader(
            title: 'Analitik',
            onBack: () =>
                context.canPop() ? context.pop() : context.go('/app/more'),
          ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  'Son 7 gün performans ve AI kullanım özeti.',
                  style: theme.textTheme.bodyMedium,
                ),
              ),
              IconButton.filledTonal(
                tooltip: 'Bugünü hesapla',
                onPressed: _isAggregating ? null : _aggregateToday,
                icon: _isAggregating
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.calculate_outlined),
              ),
            ],
          ),
          const SizedBox(height: 16),
          snapshot.when(
            data: (data) => _AnalyticsContent(snapshot: data),
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'Analitik verisi alınamadı.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }

  Future<void> _aggregateToday() async {
    setState(() => _isAggregating = true);
    try {
      await ref.read(analyticsRepositoryProvider).aggregateToday();
      ref.invalidate(analyticsSnapshotProvider);
      await ref.read(analyticsSnapshotProvider.future);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content:
                  Text(readableApiError(error, 'Hesaplama başlatılamadı.'))),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isAggregating = false);
      }
    }
  }
}

class _AnalyticsContent extends StatelessWidget {
  const _AnalyticsContent({required this.snapshot});

  final AnalyticsSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final overview = snapshot.overview;
    final avgLatency = snapshot.aiMetrics.isEmpty
        ? null
        : snapshot.aiMetrics
                .fold<double>(0, (sum, metric) => sum + metric.avgLatencyMs) /
            snapshot.aiMetrics.length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _DateRangeCard(overview: overview),
        const SizedBox(height: 14),
        GridView.count(
          crossAxisCount: 2,
          childAspectRatio: 1.35,
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          children: [
            _MetricCard(
              label: 'Tamamlanan',
              value: overview.tasksCompleted.toString(),
              icon: Icons.task_alt,
            ),
            _MetricCard(
              label: 'Geciken',
              value: overview.tasksOverdue.toString(),
              icon: Icons.warning_amber,
              accent: const Color(0xFFD97706),
            ),
            _MetricCard(
              label: 'Görüşme',
              value: overview.callsTotal.toString(),
              icon: Icons.call_outlined,
            ),
            _MetricCard(
              label: 'AI istek',
              value: overview.aiRequests.toString(),
              icon: Icons.auto_awesome,
            ),
          ],
        ),
        const SizedBox(height: 14),
        _AiCostBand(overview: overview, avgLatency: avgLatency),
        const SizedBox(height: 14),
        _TrendSection(
          title: 'Görev trendi',
          emptyMessage: 'Görev metriği yok.',
          bars: [
            for (final metric in snapshot.taskMetrics)
              _TrendBar(
                label: _shortDate(metric.date),
                value: metric.completedCount,
                secondaryValue: metric.createdCount,
              ),
          ],
        ),
        const SizedBox(height: 14),
        _TrendSection(
          title: 'Görüşme hacmi',
          emptyMessage: 'Görüşme metriği yok.',
          bars: [
            for (final metric in snapshot.callMetrics)
              _TrendBar(
                label: _shortDate(metric.date),
                value: metric.callCount,
                secondaryValue: metric.analyzedCount,
              ),
          ],
        ),
      ],
    );
  }
}

class _DateRangeCard extends StatelessWidget {
  const _DateRangeCard({required this.overview});

  final AnalyticsOverview overview;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      padding: const EdgeInsets.all(18),
      child: Row(
        children: [
          TintedIcon(icon: Icons.insights, color: theme.colorScheme.primary),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${_formatDate(overview.dateFrom)} - ${_formatDate(overview.dateTo)}',
                  style: theme.textTheme.titleMedium,
                ),
                Text(
                  'Operasyon ve AI verimlilik aralığı',
                  style: theme.textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
    this.accent = const Color(0xFF3525CD),
  });

  final String label;
  final String value;
  final IconData icon;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: accent),
          const Spacer(),
          Text(
            value,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: accent,
                  fontWeight: FontWeight.w900,
                ),
          ),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _AiCostBand extends StatelessWidget {
  const _AiCostBand({required this.overview, required this.avgLatency});

  final AnalyticsOverview overview;
  final double? avgLatency;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Row(
        children: [
          Expanded(
            child: _InlineMetric(
              label: 'AI maliyet',
              value: '\$${overview.aiCostAmount.toStringAsFixed(4)}',
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _InlineMetric(
              label: 'Ort. gecikme',
              value: avgLatency == null ? '--' : '${avgLatency!.round()} ms',
            ),
          ),
        ],
      ),
    );
  }
}

class _InlineMetric extends StatelessWidget {
  const _InlineMetric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
      ],
    );
  }
}

class _TrendSection extends StatelessWidget {
  const _TrendSection({
    required this.title,
    required this.emptyMessage,
    required this.bars,
  });

  final String title;
  final String emptyMessage;
  final List<_TrendBar> bars;

  @override
  Widget build(BuildContext context) {
    final maxValue = bars.fold<int>(
      1,
      (max, bar) => [
        max,
        bar.value,
        bar.secondaryValue,
      ].reduce((a, b) => a > b ? a : b),
    );

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          if (bars.isEmpty)
            Text(emptyMessage)
          else
            SizedBox(
              height: 132,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  for (final bar in bars)
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 3),
                        child: _TrendBarView(bar: bar, maxValue: maxValue),
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _TrendBar {
  const _TrendBar({
    required this.label,
    required this.value,
    required this.secondaryValue,
  });

  final String label;
  final int value;
  final int secondaryValue;
}

class _TrendBarView extends StatelessWidget {
  const _TrendBarView({required this.bar, required this.maxValue});

  final _TrendBar bar;
  final int maxValue;

  @override
  Widget build(BuildContext context) {
    final primaryHeight = 78 * (bar.value / maxValue);
    final secondaryHeight = 78 * (bar.secondaryValue / maxValue);

    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        SizedBox(
          height: 84,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 8,
                height: primaryHeight.clamp(2, 78),
                decoration: BoxDecoration(
                  color: const Color(0xFF3525CD),
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              const SizedBox(width: 3),
              Container(
                width: 8,
                height: secondaryHeight.clamp(2, 78),
                decoration: BoxDecoration(
                  color: const Color(0xFF8B8FA8),
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Text(
          bar.label,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context).textTheme.labelSmall,
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
    return AppCard(child: Text(message));
  }
}

String _formatDate(DateTime value) {
  return '${value.day.toString().padLeft(2, '0')}.'
      '${value.month.toString().padLeft(2, '0')}.${value.year}';
}

String _shortDate(DateTime value) {
  return '${value.day.toString().padLeft(2, '0')}.'
      '${value.month.toString().padLeft(2, '0')}';
}
