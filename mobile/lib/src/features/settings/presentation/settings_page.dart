import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/api/api_error.dart';
import '../../auth/presentation/auth_controller.dart';
import '../../email/data/email_repository.dart';
import '../../email/domain/email_models.dart';
import '../data/settings_repository.dart';
import '../domain/user_profile.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userState = ref.watch(currentUserProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(currentUserProvider);
        ref.invalidate(emailAccountsProvider);
        await ref.read(currentUserProvider.future);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Ayarlar', style: theme.textTheme.headlineMedium),
          const SizedBox(height: 16),
          userState.when(
            data: (user) => Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _ProfileCard(user: user),
                const SizedBox(height: 14),
                const _ConnectedAccountsCard(),
                const SizedBox(height: 14),
                _AccountCard(user: user),
                const SizedBox(height: 14),
                const _SupportCard(),
                const SizedBox(height: 20),
                OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: theme.colorScheme.error,
                    side: BorderSide(
                      color: theme.colorScheme.error.withValues(alpha: 0.3),
                    ),
                  ),
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

class _ConnectedAccountsCard extends ConsumerWidget {
  const _ConnectedAccountsCard();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final accounts = ref.watch(emailAccountsProvider).valueOrNull ?? const [];
    final theme = Theme.of(context);

    EmailAccount? forProvider(String provider) {
      final matches = accounts.where(
        (account) => account.provider.toLowerCase() == provider,
      );
      return matches.isEmpty ? null : matches.first;
    }

    final gmail = forProvider('gmail');
    final outlook = forProvider('outlook');

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE5E7F1)),
      ),
      child: Column(
        children: [
          _ConnectedAccountRow(
            icon: Icons.mail_outline,
            title: 'Gmail',
            subtitle: 'Kişiler ve Takvim',
            account: gmail,
            onTap: () => context.go('/app/email'),
          ),
          const Divider(height: 1),
          _ConnectedAccountRow(
            icon: Icons.cloud_outlined,
            title: 'Outlook',
            subtitle: 'E-postalar',
            account: outlook,
            onTap: () => context.go('/app/email'),
          ),
          const Divider(height: 1),
          ListTile(
            leading: Icon(Icons.calendar_month_outlined,
                color: theme.colorScheme.primary),
            title: const Text('Takvim'),
            subtitle: const Text('Randevuları görüntüle'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.go('/app/appointments'),
          ),
        ],
      ),
    );
  }
}

class _ConnectedAccountRow extends StatelessWidget {
  const _ConnectedAccountRow({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.account,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final EmailAccount? account;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isConnected = account != null &&
        account!.status.toLowerCase() != 'revoked' &&
        account!.status.toLowerCase() != 'disconnected';

    return ListTile(
      leading: Icon(icon, color: theme.colorScheme.primary),
      title: Text(title),
      subtitle: Text(account?.emailAddress ?? subtitle),
      trailing: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: (isConnected ? const Color(0xFF15803D) : theme.colorScheme.outline)
              .withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          isConnected ? 'Bağlı' : 'Bağlı değil',
          style: TextStyle(
            color: isConnected ? const Color(0xFF15803D) : theme.colorScheme.outline,
            fontWeight: FontWeight.w700,
            fontSize: 12,
          ),
        ),
      ),
      onTap: onTap,
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
            _MetricLine(label: 'E-posta', value: user.email),
            _MetricLine(
                label: 'Durum', value: _accountStatusLabel(user.status)),
            _MetricLine(
              label: 'E-posta doğrulandı',
              value: user.isEmailVerified ? 'Evet' : 'Hayır',
            ),
          ],
        ),
      ),
    );
  }
}

String _accountStatusLabel(String status) {
  return switch (status.toLowerCase()) {
    'active' => 'Aktif',
    'inactive' => 'Pasif',
    'pending' => 'Beklemede',
    'suspended' => 'Askıya alındı',
    _ => status,
  };
}

class _SupportCard extends StatelessWidget {
  const _SupportCard();

  static const _supportEmail = 'neurodeskkai@gmail.com';
  static const _supportPhone = '+905530682570';
  static const _supportPhoneDisplay = '+90 553 068 25 70';

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('İletişim', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              'Bir sorun mu yaşıyorsunuz? Bizimle iletişime geçin.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            _ContactTile(
              icon: Icons.mail_outline,
              label: 'E-posta',
              value: _supportEmail,
              onTap: () =>
                  launchUrl(Uri(scheme: 'mailto', path: _supportEmail)),
            ),
            const SizedBox(height: 8),
            _ContactTile(
              icon: Icons.call_outlined,
              label: 'Telefon',
              value: _supportPhoneDisplay,
              onTap: () => launchUrl(Uri(scheme: 'tel', path: _supportPhone)),
            ),
          ],
        ),
      ),
    );
  }
}

class _ContactTile extends StatelessWidget {
  const _ContactTile({
    required this.icon,
    required this.label,
    required this.value,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final String value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          children: [
            Icon(icon, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: Theme.of(context).textTheme.bodySmall),
                Text(
                  value,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
              ],
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
