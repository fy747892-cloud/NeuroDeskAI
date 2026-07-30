import 'package:flutter_contacts/flutter_contacts.dart' as device_contacts;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
import '../data/contacts_repository.dart';
import '../domain/contact.dart';

class ContactsPage extends ConsumerStatefulWidget {
  const ContactsPage({super.key});

  @override
  ConsumerState<ContactsPage> createState() => _ContactsPageState();
}

class _ContactsPageState extends ConsumerState<ContactsPage> {
  final _searchController = TextEditingController();
  String? _search;
  bool _isImportingDeviceContacts = false;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final contacts = ref.watch(contactsProvider(_search));
    final theme = Theme.of(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(contactsProvider(_search).future),
        child: ListView(
          padding: kScreenPadding,
          children: [
            const StitchScreenHeader(title: 'Kişiler'),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    textInputAction: TextInputAction.search,
                    onSubmitted: (_) =>
                        setState(() => _search = _searchController.text.trim()),
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.search),
                      hintText: 'Kişilerde ara...',
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: theme.colorScheme.secondary,
                  ),
                  tooltip: 'Kişi ekle',
                  onPressed: () => _showCreateContactSheet(context),
                  icon: const Icon(Icons.person_add_alt_1),
                ),
              ],
            ),
            const SizedBox(height: 10),
            FilledButton.tonalIcon(
              onPressed: _isImportingDeviceContacts
                  ? null
                  : () => _importDeviceContacts(
                        contacts.valueOrNull ?? const [],
                      ),
              icon: _isImportingDeviceContacts
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.contacts_outlined),
              label: Text(
                _isImportingDeviceContacts
                    ? 'Rehber aktarılıyor'
                    : 'Telefon rehberinden içe aktar',
              ),
            ),
            const SizedBox(height: 20),
            contacts.when(
              data: (items) => items.isEmpty
                  ? const _PageMessage(message: 'Kişi kaydı yok.')
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (_search == null || _search!.isEmpty) ...[
                          _RecentContactsStrip(contacts: items),
                          const SizedBox(height: 20),
                        ],
                        _GroupedContactList(contacts: items),
                      ],
                    ),
              error: (error, stackTrace) => _PageMessage(
                message: readableApiError(error, 'Kişiler alınamadı.'),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showCreateContactSheet(BuildContext context) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => const _CreateContactSheet(),
    );
    ref.invalidate(contactsProvider(_search));
  }

  Future<void> _importDeviceContacts(List<Contact> existingContacts) async {
    setState(() => _isImportingDeviceContacts = true);

    try {
      final granted = await device_contacts.FlutterContacts.requestPermission(
        readonly: true,
      );
      if (!granted) {
        _showSnack('Rehber izni verilmedi.');
        return;
      }

      final deviceContacts = await device_contacts.FlutterContacts.getContacts(
        withProperties: true,
      );
      final existingKeys = {
        for (final contact in existingContacts) ...[
          if (contact.email != null) _normalizeEmail(contact.email!),
          if (contact.phone != null) _normalizePhone(contact.phone!),
        ],
      }..removeWhere((key) => key.isEmpty);

      var importedCount = 0;
      var skippedCount = 0;
      for (final contact in deviceContacts) {
        final name = contact.displayName.trim();
        final phone = contact.phones.isEmpty ? '' : contact.phones.first.number;
        final email = contact.emails.isEmpty ? '' : contact.emails.first.address;
        final key = _normalizeEmail(email).isNotEmpty
            ? _normalizeEmail(email)
            : _normalizePhone(phone);

        if (name.isEmpty || key.isEmpty || existingKeys.contains(key)) {
          skippedCount++;
          continue;
        }

        await ref.read(contactsRepositoryProvider).createContact(
              fullName: name,
              email: email,
              phone: phone,
              company: contact.organizations.isEmpty
                  ? ''
                  : contact.organizations.first.company,
              title: contact.organizations.isEmpty
                  ? ''
                  : contact.organizations.first.title,
            );
        existingKeys.add(key);
        importedCount++;
      }

      ref.invalidate(contactsProvider(_search));
      _showSnack(
        importedCount == 0
            ? 'Aktarılacak yeni kişi bulunamadı.'
            : '$importedCount kişi içe aktarıldı. $skippedCount kayıt atlandı.',
      );
    } catch (error) {
      _showSnack(readableApiError(error, 'Rehber içe aktarılamadı.'));
    } finally {
      if (mounted) {
        setState(() => _isImportingDeviceContacts = false);
      }
    }
  }

  void _showSnack(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }
}

/// Stitch's mockup shows a "Favoriler" quick-access strip, but the backend
/// Contact model has no favorite flag -- fabricating one would misrepresent
/// real data. This reuses the same avatar-strip visual, honestly sourced
/// from the most recently added contacts instead.
class _RecentContactsStrip extends StatelessWidget {
  const _RecentContactsStrip({required this.contacts});

  final List<Contact> contacts;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final recent = [...contacts]
      ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
    final shown = recent.take(8).toList(growable: false);
    if (shown.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'SON EKLENENLER',
          style: TextStyle(
            color: theme.colorScheme.outline,
            fontWeight: FontWeight.w700,
            fontSize: 11,
            letterSpacing: 1,
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 78,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: shown.length,
            separatorBuilder: (context, index) => const SizedBox(width: 16),
            itemBuilder: (context, index) {
              final contact = shown[index];
              return GestureDetector(
                onTap: () => context.go('/app/contacts/${contact.id}'),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 56,
                      height: 56,
                      padding: const EdgeInsets.all(2),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: theme.colorScheme.primary, width: 2),
                      ),
                      child: CircleAvatar(
                        backgroundColor: theme.colorScheme.surfaceContainerHigh,
                        child: Text(
                          _initials(contact.fullName),
                          style: TextStyle(
                            color: theme.colorScheme.primary,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      contact.fullName.split(' ').first,
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  String _initials(String name) {
    final parts = name.split(' ').where((part) => part.isNotEmpty);
    return parts.map((part) => part[0]).take(2).join().toUpperCase();
  }
}

class _GroupedContactList extends StatelessWidget {
  const _GroupedContactList({required this.contacts});

  final List<Contact> contacts;

  @override
  Widget build(BuildContext context) {
    final sorted = [...contacts]
      ..sort((a, b) =>
          a.fullName.toLowerCase().compareTo(b.fullName.toLowerCase()));

    final groups = <String, List<Contact>>{};
    for (final contact in sorted) {
      final letter = contact.fullName.trim().isEmpty
          ? '#'
          : contact.fullName.trim()[0].toUpperCase();
      groups.putIfAbsent(letter, () => []).add(contact);
    }

    final letters = groups.keys.toList()..sort();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final letter in letters) ...[
          Padding(
            padding: const EdgeInsets.only(bottom: 8, top: 4),
            child: Row(
              children: [
                Text(
                  letter,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Theme.of(context).colorScheme.primary,
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(width: 10),
                const Expanded(child: Divider()),
              ],
            ),
          ),
          for (final contact in groups[letter]!) ...[
            _ContactCard(contact: contact),
            const SizedBox(height: 8),
          ],
          const SizedBox(height: 8),
        ],
      ],
    );
  }
}

class _ContactCard extends ConsumerWidget {
  const _ContactCard({required this.contact});

  final Contact contact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AppCard(
      padding: EdgeInsets.zero,
      onTap: () => context.go('/app/contacts/${contact.id}'),
      child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              _Avatar(name: contact.fullName),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      contact.fullName,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 3),
                    Text(
                      [contact.title, contact.company]
                              .where(
                                  (value) => value != null && value.isNotEmpty)
                              .join(' - ')
                              .trim()
                              .isEmpty
                          ? (contact.email ?? contact.phone ?? 'Profil detayı yok')
                          : [contact.title, contact.company]
                              .where(
                                  (value) => value != null && value.isNotEmpty)
                              .join(' - '),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              if (contact.phone?.trim().isNotEmpty == true)
                IconButton.filledTonal(
                  tooltip: 'Ara',
                  onPressed: () => _callPhoneNumber(context, contact.phone!),
                  icon: const Icon(Icons.call),
                ),
            ],
          ),
        ),
    );
  }
}

Future<void> _callPhoneNumber(
  BuildContext context,
  String phoneNumber,
) async {
  final normalized = _normalizePhone(phoneNumber);
  if (normalized.isEmpty) {
    return;
  }

  final uri = Uri(scheme: 'tel', path: normalized);
  final launched = await launchUrl(uri);
  if (!launched && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Arama uygulaması açılamadı.')),
    );
  }
}

String _normalizeEmail(String value) => value.trim().toLowerCase();

String _normalizePhone(String value) =>
    value.replaceAll(RegExp(r'[^0-9+]'), '').trim();

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
      width: 44,
      height: 44,
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

class _CreateContactSheet extends ConsumerStatefulWidget {
  const _CreateContactSheet();

  @override
  ConsumerState<_CreateContactSheet> createState() =>
      _CreateContactSheetState();
}

class _CreateContactSheetState extends ConsumerState<_CreateContactSheet> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _companyController = TextEditingController();
  final _titleController = TextEditingController();
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _companyController.dispose();
    _titleController.dispose();
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
            Text('Kişi ekle', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            TextField(
              controller: _nameController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Ad soyad'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'E-posta'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _phoneController,
              keyboardType: TextInputType.phone,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Telefon'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _companyController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Şirket'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(labelText: 'Unvan'),
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

  Future<void> _submit() async {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      setState(() => _errorMessage = 'Ad soyad zorunlu.');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      await ref.read(contactsRepositoryProvider).createContact(
            fullName: name,
            email: _emailController.text,
            phone: _phoneController.text,
            company: _companyController.text,
            title: _titleController.text,
          );
      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (error) {
      setState(() {
        _errorMessage = readableApiError(error, 'Kişi kaydedilemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
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
