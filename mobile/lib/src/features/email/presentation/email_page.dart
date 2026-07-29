import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/api/api_error.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/screen_header.dart';
import '../data/email_repository.dart';
import '../domain/email_models.dart';

class EmailPage extends ConsumerStatefulWidget {
  const EmailPage({super.key});

  @override
  ConsumerState<EmailPage> createState() => _EmailPageState();
}

class _EmailPageState extends ConsumerState<EmailPage>
    with WidgetsBindingObserver {
  String? _selectedAccountId;
  String? _notice;
  String? _activeAction;
  String? _pendingOAuthProvider;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed || _pendingOAuthProvider == null) {
      return;
    }
    final provider = _pendingOAuthProvider!;
    _pendingOAuthProvider = null;
    ref.invalidate(emailAccountsProvider);
    if (!mounted) {
      return;
    }
    setState(() {
      _notice =
          '${_providerLabel(provider)} yetkilendirmesinden dönüldü. Hesap durumu yenileniyor.';
    });
  }

  @override
  Widget build(BuildContext context) {
    final accountsState = ref.watch(emailAccountsProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(emailAccountsProvider.future),
      child: ListView(
        padding: kScreenPadding,
        children: [
          StitchDetailHeader(
            title: 'E-posta',
            onBack: () =>
                context.canPop() ? context.pop() : context.go('/app/more'),
          ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  'Gmail ve Outlook hesaplarını takip et, mesajları senkronize et.',
                  style: theme.textTheme.bodyMedium,
                ),
              ),
              PopupMenuButton<String>(
                tooltip: 'Bağla',
                icon: const Icon(Icons.add_link),
                onSelected: _startConnect,
                itemBuilder: (context) => const [
                  PopupMenuItem(value: 'gmail', child: Text('Gmail bağla')),
                  PopupMenuItem(
                    value: 'outlook',
                    child: Text('Outlook bağla'),
                  ),
                ],
              ),
            ],
          ),
          if (_notice != null) ...[
            const SizedBox(height: 12),
            _PageMessage(message: _notice!),
          ],
          const SizedBox(height: 16),
          accountsState.when(
            data: (accounts) {
              final selectedId = _selectedAccountId ??
                  (accounts.isEmpty ? null : accounts.first.id);
              final selectedAccount = selectedId == null
                  ? null
                  : accounts
                      .where((account) => account.id == selectedId)
                      .firstOrNull;
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _EmailSummary(accounts: accounts),
                  const SizedBox(height: 14),
                  if (accounts.isEmpty)
                    const _PageMessage(message: 'Bağlı e-posta hesabı yok.')
                  else
                    ...accounts.map(
                      (account) => _AccountCard(
                        account: account,
                        isSelected: account.id == selectedId,
                        isActive: _activeAction == account.id ||
                            _activeAction == 'revoke-${account.id}',
                        onSelect: () {
                          setState(() => _selectedAccountId = account.id);
                        },
                        onSync: () => _sync(account),
                        onRevoke: () => _revoke(account),
                      ),
                    ),
                  const SizedBox(height: 10),
                  if (selectedAccount != null)
                    _MessagesPanel(account: selectedAccount),
                ],
              );
            },
            error: (error, stackTrace) => _PageMessage(
              message: readableApiError(error, 'E-posta hesapları alınamadı.'),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
          ),
        ],
      ),
    );
  }

  Future<void> _startConnect(String provider) async {
    setState(() {
      _activeAction = 'connect-$provider';
      _notice = null;
    });

    try {
      final result = await ref.read(emailRepositoryProvider).startConnect(
            provider,
            returnTo: 'neurodesk://app/oauth/email/$provider',
          );
      final opened = await launchUrl(
        Uri.parse(result.authorizeUrl),
        mode: LaunchMode.externalApplication,
      );
      setState(() {
        _pendingOAuthProvider = opened ? provider : null;
        _notice = opened
            ? '${_providerLabel(provider)} yetkilendirmesi tarayıcıda açıldı. İşlemi tamamlayıp uygulamaya dön.'
            : '${_providerLabel(provider)} yetki URL hazır: ${result.authorizeUrl}';
      });
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'E-posta bağlantısı başlatılamadı.');
      });
    } finally {
      if (mounted) {
        setState(() => _activeAction = null);
      }
    }
  }

  Future<void> _sync(EmailAccount account) async {
    setState(() {
      _activeAction = account.id;
      _notice = null;
    });

    try {
      final summary =
          await ref.read(emailRepositoryProvider).syncAccount(account.id);
      setState(() {
        _notice = 'Senkron tamam: ${summary.fetched} alındı, '
            '${summary.created} eklendi, ${summary.skipped} atlandı.';
      });
      ref.invalidate(emailAccountsProvider);
      ref.invalidate(emailMessagesProvider(account.id));
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'E-posta senkronize edilemedi.');
      });
    } finally {
      if (mounted) {
        setState(() => _activeAction = null);
      }
    }
  }

  Future<void> _revoke(EmailAccount account) async {
    setState(() {
      _activeAction = 'revoke-${account.id}';
      _notice = null;
    });

    try {
      await ref.read(emailRepositoryProvider).revokeAccount(account.id);
      setState(() => _notice = 'E-posta bağlantısı kaldırıldı.');
      ref.invalidate(emailAccountsProvider);
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'E-posta bağlantısı kaldırılamadı.');
      });
    } finally {
      if (mounted) {
        setState(() => _activeAction = null);
      }
    }
  }
}

class _EmailSummary extends StatelessWidget {
  const _EmailSummary({required this.accounts});

  final List<EmailAccount> accounts;

  @override
  Widget build(BuildContext context) {
    final connected =
        accounts.where((account) => account.status == 'connected').length;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: BentoStatTile(
            icon: Icons.mail_outline,
            label: 'Hesap',
            value: accounts.length.toString(),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: InfoTile(
            icon: Icons.link,
            label: 'Bağlı',
            text: '$connected hesap bağlı',
          ),
        ),
      ],
    );
  }
}

class _AccountCard extends StatelessWidget {
  const _AccountCard({
    required this.account,
    required this.isSelected,
    required this.isActive,
    required this.onSelect,
    required this.onSync,
    required this.onRevoke,
  });

  final EmailAccount account;
  final bool isSelected;
  final bool isActive;
  final VoidCallback onSelect;
  final VoidCallback onSync;
  final VoidCallback onRevoke;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: AppCard(
        padding: const EdgeInsets.all(14),
        onTap: onSelect,
        child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    isSelected ? Icons.radio_button_checked : Icons.mail,
                    color: const Color(0xFF3525CD),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          account.emailAddress ??
                              _providerLabel(account.provider),
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          account.lastSyncedAt == null
                              ? 'Senkron yok'
                              : 'Son: ${_formatDateTime(account.lastSyncedAt!)}',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  Chip(
                    label: Text(_emailStatusLabel(account.status)),
                    visualDensity: VisualDensity.compact,
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: isActive || account.status != 'connected'
                          ? null
                          : onSync,
                      icon: isActive
                          ? const SizedBox.square(
                              dimension: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.sync),
                      label: const Text('Senkronize et'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  IconButton.outlined(
                    tooltip: 'Bağlantıyı kaldır',
                    onPressed: isActive || account.status == 'revoked'
                        ? null
                        : onRevoke,
                    icon: const Icon(Icons.link_off),
                  ),
                ],
              ),
            ],
          ),
      ),
    );
  }
}

class _MessagesPanel extends ConsumerWidget {
  const _MessagesPanel({required this.account});

  final EmailAccount account;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final messages = ref.watch(emailMessagesProvider(account.id));

    return messages.when(
      data: (items) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Mesajlar', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 10),
          if (items.isEmpty)
            const _PageMessage(message: 'Seçili hesapta mesaj yok.')
          else
            ...items.map((message) => _MessageCard(message: message)),
        ],
      ),
      error: (error, stackTrace) => _PageMessage(
        message: readableApiError(error, 'Mesajlar alınamadı.'),
      ),
      loading: () => const LinearProgressIndicator(),
    );
  }
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({required this.message});

  final EmailMessage message;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: AppCard(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message.subject ?? 'Konu yok',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 6),
            Text(message.snippet ?? 'Ön izleme yok.'),
            const SizedBox(height: 8),
            Wrap(
              spacing: 10,
              runSpacing: 6,
              children: [
                Text(
                  message.fromAddress ?? 'Gönderen yok',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                if (message.receivedAt != null)
                  Text(
                    _formatDateTime(message.receivedAt!),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
              ],
            ),
          ],
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

String _providerLabel(String provider) {
  return switch (provider) {
    'gmail' => 'Gmail',
    'outlook' => 'Outlook',
    _ => provider,
  };
}

String _emailStatusLabel(String status) {
  return switch (status.toLowerCase()) {
    'connected' => 'Bağlı',
    'pending_oauth' => 'Yetki bekliyor',
    'revoked' => 'Bağlantı kaldırıldı',
    'failed' => 'Hata',
    _ => status,
  };
}

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
