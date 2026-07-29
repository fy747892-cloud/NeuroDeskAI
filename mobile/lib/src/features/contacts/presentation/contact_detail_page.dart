import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../data/contacts_repository.dart';
import '../domain/contact.dart';

class ContactDetailPage extends ConsumerStatefulWidget {
  const ContactDetailPage({required this.contactId, super.key});

  final String contactId;

  @override
  ConsumerState<ContactDetailPage> createState() => _ContactDetailPageState();
}

class _ContactDetailPageState extends ConsumerState<ContactDetailPage> {
  final _noteController = TextEditingController();
  bool _isAddingNote = false;
  String? _noteError;

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final detail = ref.watch(contactDetailProvider(widget.contactId));
    final memory = ref.watch(contactMemoryProvider(widget.contactId));

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(contactDetailProvider(widget.contactId));
        ref.invalidate(contactMemoryProvider(widget.contactId));
      },
      child: ListView(
        padding: kScreenPadding,
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton.icon(
              onPressed: () => context.go('/app/contacts'),
              icon: const Icon(Icons.arrow_back),
              label: const Text('Kişi listesi'),
            ),
          ),
          detail.when(
            data: (contact) => Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _ProfileCard(contact: contact),
                const SizedBox(height: 14),
                memory.when(
                  data: (value) => _MemoryCard(memory: value),
                  error: (error, stackTrace) => _PageMessage(
                    message: readableApiError(error, 'Hafıza alınamadı.'),
                  ),
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                ),
                const SizedBox(height: 14),
                _NotesCard(
                  notes: contact.notes,
                  controller: _noteController,
                  isSubmitting: _isAddingNote,
                  errorMessage: _noteError,
                  onSubmit: _addNote,
                ),
                const SizedBox(height: 14),
                _TimelineCard(events: contact.recentTimeline),
              ],
            ),
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'Kişi bilgisi alınamadı.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }

  Future<void> _addNote() async {
    final text = _noteController.text.trim();
    if (text.isEmpty) {
      setState(() => _noteError = 'Not metni zorunlu.');
      return;
    }

    setState(() {
      _isAddingNote = true;
      _noteError = null;
    });

    try {
      await ref
          .read(contactsRepositoryProvider)
          .addNote(widget.contactId, text);
      _noteController.clear();
      ref.invalidate(contactDetailProvider(widget.contactId));
    } catch (error) {
      setState(() {
        _noteError = readableApiError(error, 'Not eklenemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isAddingNote = false);
      }
    }
  }
}

class _ProfileCard extends StatelessWidget {
  const _ProfileCard({required this.contact});

  final ContactDetail contact;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.all(18),
      child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _Avatar(name: contact.fullName),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        contact.fullName,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        [contact.title, contact.company]
                                .where(
                                  (value) =>
                                      value != null && value.trim().isNotEmpty,
                                )
                                .join(', ')
                                .trim()
                                .isEmpty
                            ? contact.status
                            : [contact.title, contact.company]
                                .where(
                                  (value) =>
                                      value != null && value.trim().isNotEmpty,
                                )
                                .join(', '),
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            if (contact.email != null)
              _InfoLine(icon: Icons.mail, text: contact.email!),
            if (contact.phone != null)
              _InfoLine(icon: Icons.phone, text: contact.phone!),
          ],
      ),
    );
  }
}

class _MemoryCard extends StatelessWidget {
  const _MemoryCard({required this.memory});

  final ContactMemory memory;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome, size: 18, color: theme.colorScheme.primary),
              const SizedBox(width: 8),
              Text(
                'Müşteri Hafızası',
                style: theme.textTheme.titleMedium?.copyWith(color: theme.colorScheme.primary),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _MemoryMetric(
                  label: 'Açık görev',
                  value: memory.pendingItemsCount.toString(),
                ),
              ),
              Expanded(
                child: _MemoryMetric(
                  label: 'Fırsat',
                  value: memory.openDealsCount.toString(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _MemoryLine(
            label: 'Son görüşme',
            value: memory.lastConversationTitle ?? 'Kayıt yok',
          ),
          _MemoryLine(
            label: 'Sonraki randevu',
            value: memory.nextAppointmentTitle ?? 'Plan yok',
          ),
          if (memory.lastTopic != null)
            _MemoryLine(label: 'Son konu', value: memory.lastTopic!),
        ],
      ),
    );
  }
}

class _MemoryMetric extends StatelessWidget {
  const _MemoryMetric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
        ),
        Text(label, style: theme.textTheme.bodySmall),
      ],
    );
  }
}

class _MemoryLine extends StatelessWidget {
  const _MemoryLine({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Text(
        '$label: $value',
        style: Theme.of(context).textTheme.bodySmall,
      ),
    );
  }
}

class _NotesCard extends StatelessWidget {
  const _NotesCard({
    required this.notes,
    required this.controller,
    required this.isSubmitting,
    required this.onSubmit,
    this.errorMessage,
  });

  final List<ContactNote> notes;
  final TextEditingController controller;
  final bool isSubmitting;
  final String? errorMessage;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.all(14),
      child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Notlar', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            if (notes.isEmpty)
              Text('Henüz not yok.',
                  style: Theme.of(context).textTheme.bodySmall)
            else
              ...notes.map((note) => _NoteItem(note: note)),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              minLines: 2,
              maxLines: 4,
              decoration: const InputDecoration(labelText: 'Yeni not'),
            ),
            if (errorMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                onPressed: isSubmitting ? null : onSubmit,
                icon: const Icon(Icons.save),
                label: Text(isSubmitting ? 'Ekleniyor' : 'Not ekle'),
              ),
            ),
          ],
      ),
    );
  }
}

class _NoteItem extends StatelessWidget {
  const _NoteItem({required this.note});

  final ContactNote note;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainer,
        borderRadius: BorderRadius.circular(kCardRadius),
      ),
      child: Text(note.noteText),
    );
  }
}

class _TimelineCard extends StatelessWidget {
  const _TimelineCard({required this.events});

  final List<ContactTimelineEvent> events;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Son hareketler', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          if (events.isEmpty)
            Text(
              'Zaman çizelgesi kaydı yok.',
              style: Theme.of(context).textTheme.bodySmall,
            )
          else
            ...events.map((event) => _TimelineItem(event: event)),
        ],
      ),
    );
  }
}

class _TimelineItem extends StatelessWidget {
  const _TimelineItem({required this.event});

  final ContactTimelineEvent event;

  @override
  Widget build(BuildContext context) {
    final title = event.eventMetadata?['title'] as String? ?? event.eventType;

    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: const Icon(Icons.history),
      title: Text(title),
      subtitle: Text(event.sourceType ?? event.eventType),
      dense: true,
    );
  }
}

class _InfoLine extends StatelessWidget {
  const _InfoLine({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        children: [
          Icon(icon, size: 16, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 8),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.name});

  final String name;

  @override
  Widget build(BuildContext context) {
    final initials = name
        .split(' ')
        .where((part) => part.isNotEmpty)
        .map((part) => part[0])
        .take(2)
        .join()
        .toUpperCase();

    return Container(
      width: 54,
      height: 54,
      decoration: BoxDecoration(
        color: const Color(0x1A3525CD),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Center(
        child: Text(
          initials.isEmpty ? '?' : initials,
          style: const TextStyle(
            color: Color(0xFF3525CD),
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
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
