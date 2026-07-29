import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../data/appointments_repository.dart';
import '../domain/appointment.dart';

class AppointmentsPage extends ConsumerStatefulWidget {
  const AppointmentsPage({super.key});

  @override
  ConsumerState<AppointmentsPage> createState() => _AppointmentsPageState();
}

class _AppointmentsPageState extends ConsumerState<AppointmentsPage> {
  late DateTime _visibleMonth = DateTime(DateTime.now().year, DateTime.now().month);
  late DateTime _selectedDay = _dateOnly(DateTime.now());

  @override
  Widget build(BuildContext context) {
    final appointments = ref.watch(appointmentsForMonthProvider(_visibleMonth));
    final theme = Theme.of(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(appointmentsForMonthProvider(_visibleMonth).future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Takvim', style: theme.textTheme.headlineMedium),
            const SizedBox(height: 16),
            appointments.when(
              data: (items) => Column(
                children: [
                  _MonthCalendar(
                    visibleMonth: _visibleMonth,
                    selectedDay: _selectedDay,
                    appointments: items,
                    onMonthChanged: (month) =>
                        setState(() => _visibleMonth = month),
                    onDaySelected: (day) => setState(() => _selectedDay = day),
                  ),
                  const SizedBox(height: 18),
                  _DayAgenda(
                    day: _selectedDay,
                    appointments: items
                        .where((a) => _dateOnly(a.startAt.toLocal()) == _selectedDay)
                        .toList(growable: false)
                      ..sort((a, b) => a.startAt.compareTo(b.startAt)),
                    onAdd: () => _showCreateSheet(context, ref),
                  ),
                ],
              ),
              error: (error, stackTrace) => _EmptyList(
                message: readableApiError(error, 'Randevular alınamadı.'),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Randevu ekle',
        onPressed: () => _showCreateSheet(context, ref),
        child: const Icon(Icons.add),
      ),
    );
  }

  Future<void> _showCreateSheet(BuildContext context, WidgetRef ref) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => _CreateAppointmentSheet(initialDay: _selectedDay),
    );
    ref.invalidate(appointmentsForMonthProvider(_visibleMonth));
  }
}

DateTime _dateOnly(DateTime value) => DateTime(value.year, value.month, value.day);

class _MonthCalendar extends StatelessWidget {
  const _MonthCalendar({
    required this.visibleMonth,
    required this.selectedDay,
    required this.appointments,
    required this.onMonthChanged,
    required this.onDaySelected,
  });

  final DateTime visibleMonth;
  final DateTime selectedDay;
  final List<Appointment> appointments;
  final ValueChanged<DateTime> onMonthChanged;
  final ValueChanged<DateTime> onDaySelected;

  static const _monthNames = [
    'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
    'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık',
  ];
  static const _weekdayLabels = ['Pt', 'Sa', 'Ça', 'Pe', 'Cu', 'Ct', 'Pz'];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final firstOfMonth = DateTime(visibleMonth.year, visibleMonth.month, 1);
    final daysInMonth = DateTime(visibleMonth.year, visibleMonth.month + 1, 0).day;
    final leadingBlanks = (firstOfMonth.weekday - DateTime.monday) % 7;

    final daysWithAppointments = appointments
        .map((a) => _dateOnly(a.startAt.toLocal()))
        .toSet();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE5E7F1)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${_monthNames[visibleMonth.month - 1]} ${visibleMonth.year}',
                style: theme.textTheme.titleMedium,
              ),
              Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.chevron_left),
                    onPressed: () => onMonthChanged(
                      DateTime(visibleMonth.year, visibleMonth.month - 1),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.chevron_right),
                    onPressed: () => onMonthChanged(
                      DateTime(visibleMonth.year, visibleMonth.month + 1),
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          GridView.count(
            crossAxisCount: 7,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            children: [
              for (final label in _weekdayLabels)
                Center(
                  child: Text(
                    label,
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.outline,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              for (var i = 0; i < leadingBlanks; i++) const SizedBox.shrink(),
              for (var day = 1; day <= daysInMonth; day++)
                _DayCell(
                  day: day,
                  date: DateTime(visibleMonth.year, visibleMonth.month, day),
                  isSelected: DateTime(visibleMonth.year, visibleMonth.month, day) ==
                      selectedDay,
                  hasAppointment: daysWithAppointments
                      .contains(DateTime(visibleMonth.year, visibleMonth.month, day)),
                  onTap: () => onDaySelected(
                    DateTime(visibleMonth.year, visibleMonth.month, day),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DayCell extends StatelessWidget {
  const _DayCell({
    required this.day,
    required this.date,
    required this.isSelected,
    required this.hasAppointment,
    required this.onTap,
  });

  final int day;
  final DateTime date;
  final bool isSelected;
  final bool hasAppointment;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isToday = date == _dateOnly(DateTime.now());

    return InkWell(
      onTap: onTap,
      customBorder: const CircleBorder(),
      child: Padding(
        padding: const EdgeInsets.all(2),
        child: Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isSelected ? theme.colorScheme.primary : null,
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '$day',
                  style: TextStyle(
                    color: isSelected
                        ? Colors.white
                        : (isToday ? theme.colorScheme.primary : null),
                    fontWeight:
                        isSelected || isToday ? FontWeight.w800 : FontWeight.normal,
                  ),
                ),
                if (hasAppointment && !isSelected)
                  Container(
                    width: 4,
                    height: 4,
                    margin: const EdgeInsets.only(top: 2),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary,
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _DayAgenda extends StatelessWidget {
  const _DayAgenda({
    required this.day,
    required this.appointments,
    required this.onAdd,
  });

  final DateTime day;
  final List<Appointment> appointments;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(_formatDayHeader(day), style: theme.textTheme.titleMedium),
        const SizedBox(height: 10),
        if (appointments.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: theme.colorScheme.outlineVariant,
                width: 1.4,
              ),
            ),
            child: Column(
              children: [
                Icon(Icons.event_busy, color: theme.colorScheme.outline, size: 32),
                const SizedBox(height: 10),
                Text('Bugün için planlanmış bir şey yok',
                    style: theme.textTheme.bodyMedium),
                const SizedBox(height: 14),
                FilledButton.icon(
                  onPressed: onAdd,
                  icon: const Icon(Icons.add),
                  label: const Text('Randevu Ekle'),
                ),
              ],
            ),
          )
        else
          ...appointments.map((appointment) => _AppointmentCard(appointment: appointment)),
      ],
    );
  }

  String _formatDayHeader(DateTime day) {
    const months = [
      'Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz',
      'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara',
    ];
    return '${day.day} ${months[day.month - 1]} ${day.year}';
  }
}

class _AppointmentCard extends ConsumerWidget {
  const _AppointmentCard({required this.appointment});

  final Appointment appointment;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border(
          left: BorderSide(color: theme.colorScheme.primary, width: 4),
          top: const BorderSide(color: Color(0xFFE5E7F1)),
          right: const BorderSide(color: Color(0xFFE5E7F1)),
          bottom: const BorderSide(color: Color(0xFFE5E7F1)),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              Text(
                _formatTime(appointment.startAt),
                style: theme.textTheme.titleMedium?.copyWith(
                  color: theme.colorScheme.primary,
                  fontWeight: FontWeight.w800,
                ),
              ),
              Text(_formatTime(appointment.endAt), style: theme.textTheme.bodySmall),
            ],
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(appointment.title, style: theme.textTheme.titleMedium),
                if (appointment.location != null && appointment.location!.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(appointment.location!, style: theme.textTheme.bodySmall),
                  ),
              ],
            ),
          ),
          PopupMenuButton<String>(
            onSelected: (value) async {
              if (value == 'delete') {
                await ref
                    .read(appointmentsRepositoryProvider)
                    .deleteAppointment(appointment.id);
                ref.invalidate(appointmentsForMonthProvider(
                  DateTime(appointment.startAt.year, appointment.startAt.month),
                ));
              }
            },
            itemBuilder: (context) => const [
              PopupMenuItem(value: 'delete', child: Text('Sil')),
            ],
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime value) {
    final local = value.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _CreateAppointmentSheet extends ConsumerStatefulWidget {
  const _CreateAppointmentSheet({required this.initialDay});

  final DateTime initialDay;

  @override
  ConsumerState<_CreateAppointmentSheet> createState() =>
      _CreateAppointmentSheetState();
}

class _CreateAppointmentSheetState
    extends ConsumerState<_CreateAppointmentSheet> {
  final _titleController = TextEditingController();
  final _locationController = TextEditingController();
  late TimeOfDay _startTime = TimeOfDay.now();
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _titleController.dispose();
    _locationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.viewInsetsOf(context).bottom;

    return Padding(
      padding: EdgeInsets.fromLTRB(16, 16, 16, 16 + bottomInset),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Randevu ekle', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(labelText: 'Başlık'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _locationController,
              decoration: const InputDecoration(labelText: 'Konum (opsiyonel)'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _pickStartTime,
              icon: const Icon(Icons.schedule),
              label: Text('Saat: ${_startTime.format(context)}'),
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 10),
              Text(
                _errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _isSubmitting ? null : _submit,
                icon: const Icon(Icons.save),
                label: Text(_isSubmitting ? 'Kaydediliyor' : 'Kaydet'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickStartTime() async {
    final picked = await showTimePicker(context: context, initialTime: _startTime);
    if (picked != null) setState(() => _startTime = picked);
  }

  Future<void> _submit() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      setState(() => _errorMessage = 'Başlık zorunlu.');
      return;
    }

    final startAt = DateTime(
      widget.initialDay.year,
      widget.initialDay.month,
      widget.initialDay.day,
      _startTime.hour,
      _startTime.minute,
    );

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });
    try {
      await ref.read(appointmentsRepositoryProvider).createAppointment(
            title: title,
            startAt: startAt,
            endAt: startAt.add(const Duration(minutes: 30)),
            location: _locationController.text.trim(),
          );
      if (mounted) Navigator.of(context).pop();
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Randevu eklenemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
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
