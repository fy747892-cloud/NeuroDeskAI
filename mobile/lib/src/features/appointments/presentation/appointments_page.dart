import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/appointments_repository.dart';
import '../domain/appointment.dart';

class AppointmentsPage extends ConsumerWidget {
  const AppointmentsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appointments = ref.watch(appointmentsProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(appointmentsProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Takvim', style: theme.textTheme.headlineMedium),
          const SizedBox(height: 6),
          Text(
            'Yaklaşan görüşme, toplantı ve takipleri tek akış halinde izle.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          appointments.when(
            data: (items) => items.isEmpty
                ? const _EmptyList(message: 'Yaklaşan randevu yok.')
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _CalendarSummary(appointments: items),
                      const SizedBox(height: 14),
                      ...items.map(
                        (appointment) =>
                            _AppointmentTile(appointment: appointment),
                      ),
                    ],
                  ),
            error: (error, stackTrace) =>
                const _EmptyList(message: 'Randevular alınamadı.'),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

class _CalendarSummary extends StatelessWidget {
  const _CalendarSummary({required this.appointments});

  final List<Appointment> appointments;

  @override
  Widget build(BuildContext context) {
    final today = DateTime.now();
    final todayCount = appointments.where((appointment) {
      final date = appointment.startAt.toLocal();
      return date.year == today.year &&
          date.month == today.month &&
          date.day == today.day;
    }).length;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF3525CD),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: _SummaryMetric(
              label: 'Yaklaşan',
              value: appointments.length.toString(),
              icon: Icons.event_available,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Bugün',
              value: todayCount.toString(),
              icon: Icons.today,
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

class _AppointmentTile extends StatelessWidget {
  const _AppointmentTile({required this.appointment});

  final Appointment appointment;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _DateBadge(date: appointment.startAt),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          appointment.title,
                          style: theme.textTheme.titleMedium,
                        ),
                      ),
                      _StatusChip(status: appointment.status),
                    ],
                  ),
                  const SizedBox(height: 8),
                  _MetaLine(
                    icon: Icons.schedule,
                    text:
                        '${_formatTime(appointment.startAt)} - ${_formatTime(appointment.endAt)}',
                  ),
                  if (appointment.location != null &&
                      appointment.location!.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    _MetaLine(
                      icon: Icons.place_outlined,
                      text: appointment.location!,
                    ),
                  ],
                  if (appointment.description != null &&
                      appointment.description!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      appointment.description!,
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime value) {
    final local = value.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _DateBadge extends StatelessWidget {
  const _DateBadge({required this.date});

  final DateTime date;

  @override
  Widget build(BuildContext context) {
    final local = date.toLocal();

    return Container(
      width: 56,
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFFF4F5FB),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE5E7F1)),
      ),
      child: Column(
        children: [
          Text(
            local.day.toString().padLeft(2, '0'),
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: const Color(0xFF3525CD),
                  fontWeight: FontWeight.w800,
                ),
          ),
          Text(
            _monthLabel(local.month),
            style: Theme.of(context).textTheme.labelSmall,
          ),
        ],
      ),
    );
  }

  String _monthLabel(int month) {
    return const [
      'Oca',
      'Şub',
      'Mar',
      'Nis',
      'May',
      'Haz',
      'Tem',
      'Ağu',
      'Eyl',
      'Eki',
      'Kas',
      'Ara',
    ][month - 1];
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

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final label = switch (status.toLowerCase()) {
      'confirmed' => 'Onaylı',
      'scheduled' => 'Planlı',
      'cancelled' => 'Iptal',
      'completed' => 'Bitti',
      _ => status,
    };

    return Chip(
      label: Text(label),
      visualDensity: VisualDensity.compact,
    );
  }
}

class _EmptyList extends StatelessWidget {
  const _EmptyList({required this.message});

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
