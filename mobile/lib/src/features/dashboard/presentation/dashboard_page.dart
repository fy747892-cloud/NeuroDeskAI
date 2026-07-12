import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/dashboard_repository.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(dashboardProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Dashboard', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 16),
          dashboard.when(
            data: (data) => GridView.count(
              crossAxisCount: MediaQuery.sizeOf(context).width > 640 ? 4 : 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _MetricCard(label: 'Acik gorev', value: data.summary.openTasksCount),
                _MetricCard(label: 'Gecikmis', value: data.summary.overdueTasksCount),
                _MetricCard(
                  label: 'Randevu',
                  value: data.summary.upcomingAppointmentsCount,
                ),
                _MetricCard(
                  label: 'AI onay',
                  value: data.summary.pendingAiApprovalsCount,
                ),
              ],
            ),
            error: (error, stackTrace) => const _PageMessage(
              title: 'Dashboard alinamadi',
              body: 'Baglantiyi kontrol edip tekrar dene.',
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: Theme.of(context).textTheme.labelLarge),
            Text('$value', style: Theme.of(context).textTheme.headlineMedium),
          ],
        ),
      ),
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
