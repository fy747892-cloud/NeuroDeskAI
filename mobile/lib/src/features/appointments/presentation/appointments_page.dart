import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/appointments_repository.dart';
import '../domain/appointment.dart';

class AppointmentsPage extends ConsumerWidget {
  const AppointmentsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appointments = ref.watch(appointmentsProvider);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(appointmentsProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Takvim', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 16),
          appointments.when(
            data: (items) => items.isEmpty
                ? const _EmptyList(message: 'Yaklasan randevu yok.')
                : Column(
                    children: items
                        .map((appointment) => _AppointmentTile(appointment: appointment))
                        .toList(growable: false),
                  ),
            error: (error, stackTrace) => const _EmptyList(message: 'Randevular alinamadi.'),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

class _AppointmentTile extends StatelessWidget {
  const _AppointmentTile({required this.appointment});

  final Appointment appointment;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        title: Text(appointment.title),
        subtitle: Text(appointment.location ?? appointment.description ?? appointment.status),
        trailing: Text(_formatTime(appointment.startAt)),
      ),
    );
  }

  String _formatTime(DateTime value) {
    return '${value.day.toString().padLeft(2, '0')}.${value.month.toString().padLeft(2, '0')} '
        '${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';
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
