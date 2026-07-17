import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/api_error.dart';
import '../../../core/api/api_status.dart';
import '../../auth/presentation/auth_controller.dart';
import '../data/settings_repository.dart';
import '../domain/user_profile.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userState = ref.watch(currentUserProvider);
    final apiStatus = ref.watch(apiStatusProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(currentUserProvider);
        ref.invalidate(apiStatusProvider);
        await ref.read(currentUserProvider.future);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Ayarlar', style: theme.textTheme.headlineMedium),
          const SizedBox(height: 6),
          Text(
            'Hesap, profil ve mobil bağlantı durumunu yönet.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          userState.when(
            data: (user) => Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _ProfileCard(user: user),
                const SizedBox(height: 12),
                _ApiCard(apiStatus: apiStatus),
                const SizedBox(height: 12),
                _AccountCard(user: user),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: () {
                    ref.read(authControllerProvider.notifier).logout();
                  },
                  icon: const Icon(Icons.logout),
                  label: const Text('Çıkış yap'),
                ),
              ],
            ),
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'Ayarlar alınamadı.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }
}

class _ProfileCard extends ConsumerStatefulWidget {
  const _ProfileCard({required this.user});

  final CurrentUser user;

  @override
  ConsumerState<_ProfileCard> createState() => _ProfileCardState();
}

class _ProfileCardState extends ConsumerState<_ProfileCard> {
  late final TextEditingController _fullNameController;
  late final TextEditingController _titleController;
  bool _isSaving = false;
  String? _message;

  @override
  void initState() {
    super.initState();
    _fullNameController = TextEditingController(
      text: widget.user.profile?.fullName ?? widget.user.email,
    );
    _titleController = TextEditingController(text: widget.user.profile?.title);
  }

  @override
  void dispose() {
    _fullNameController.dispose();
    _titleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Profil', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            TextField(
              controller: _fullNameController,
              decoration: const InputDecoration(
                labelText: 'Ad soyad',
                prefixIcon: Icon(Icons.person_outline),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: 'Unvan',
                prefixIcon: Icon(Icons.badge_outlined),
              ),
            ),
            if (_message != null) ...[
              const SizedBox(height: 10),
              Text(_message!),
            ],
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _isSaving ? null : _save,
              icon: _isSaving
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.save_outlined),
              label: const Text('Profili kaydet'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _save() async {
    final fullName = _fullNameController.text.trim();
    if (fullName.isEmpty) {
      setState(() => _message = 'Ad soyad zorunlu.');
      return;
    }

    setState(() {
      _isSaving = true;
      _message = null;
    });
    try {
      await ref.read(settingsRepositoryProvider).updateProfile(
            fullName: fullName,
            title: _titleController.text,
          );
      ref.invalidate(currentUserProvider);
      setState(() => _message = 'Profil güncellendi.');
    } catch (error) {
      setState(() {
        _message = readableApiError(error, 'Profil güncellenemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }
}

class _ApiCard extends StatelessWidget {
  const _ApiCard({required this.apiStatus});

  final AsyncValue<ApiStatus> apiStatus;

  @override
  Widget build(BuildContext context) {
    final statusLabel = apiStatus.when(
      data: (status) => status.displayLabel,
      error: (error, stackTrace) => 'Bağlantı hatası',
      loading: () => 'Kontrol ediliyor',
    );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('API bağlantısı',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 10),
            _MetricLine(label: 'Durum', value: statusLabel),
            _MetricLine(label: 'Base URL', value: apiBaseUrl),
          ],
        ),
      ),
    );
  }
}

class _AccountCard extends StatelessWidget {
  const _AccountCard({required this.user});

  final CurrentUser user;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Hesap', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 10),
            _MetricLine(label: 'Email', value: user.email),
            _MetricLine(label: 'Durum', value: user.status),
            _MetricLine(
              label: 'Email dogrulandi',
              value: user.isEmailVerified ? 'Evet' : 'Hayir',
            ),
            _MetricLine(label: 'Tenant', value: user.tenantId),
            _MetricLine(
              label: 'Organizasyon',
              value: user.organizationId ?? 'Yok',
            ),
          ],
        ),
      ),
    );
  }
}

class _MetricLine extends StatelessWidget {
  const _MetricLine({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 118,
            child: Text(label, style: Theme.of(context).textTheme.bodySmall),
          ),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
        ],
      ),
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
