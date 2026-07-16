import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../data/email_repository.dart';
import '../domain/email_models.dart';

class EmailPage extends ConsumerStatefulWidget {
  const EmailPage({super.key});

  @override
  ConsumerState<EmailPage> createState() => _EmailPageState();
}

class _EmailPageState extends ConsumerState<EmailPage> {
  String? _selectedAccountId;
  String? _notice;
  String? _activeAction;

  @override
  Widget build(BuildContext context) {
    final accountsState = ref.watch(emailAccountsProvider);
    final theme = Theme.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(emailAccountsProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('E-posta', style: theme.textTheme.headlineMedium),
                    const SizedBox(height: 6),
                    Text(
                      'Gmail ve Outlook hesaplarini takip et, mesajlari senkronize et.',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              PopupMenuButton<String>(
                tooltip: 'Bagla',
                icon: const Icon(Icons.add_link),
                onSelected: _startConnect,
                itemBuilder: (context) => const [
                  PopupMenuItem(value: 'gmail', child: Text('Gmail bagla')),
                  PopupMenuItem(
                    value: 'outlook',
                    child: Text('Outlook bagla'),
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
                    const _PageMessage(message: 'Bagli e-posta hesabi yok.')
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
              message: readableApiError(error, 'E-posta hesaplari alinamadi.'),
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
          );
      setState(() {
        _notice = '${_providerLabel(provider)} yetki URL hazir: '
            '${result.authorizeUrl}';
      });
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'E-posta baglantisi baslatilamadi.');
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
        _notice = 'Senkron tamam: ${summary.fetched} alindi, '
            '${summary.created} eklendi, ${summary.skipped} atlandi.';
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
      setState(() => _notice = 'E-posta baglantisi kaldirildi.');
      ref.invalidate(emailAccountsProvider);
    } catch (error) {
      setState(() {
        _notice = readableApiError(error, 'E-posta baglantisi kaldirilamadi.');
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

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF17152F),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: _SummaryMetric(
              label: 'Hesap',
              value: accounts.length.toString(),
              icon: Icons.mail_outline,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _SummaryMetric(
              label: 'Bagli',
              value: connected.toString(),
              icon: Icons.link,
            ),
          ),
        ],
      ),
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
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onSelect,
        child: Padding(
          padding: const EdgeInsets.all(14),
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
                    label: Text(account.status),
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
                    tooltip: 'Baglantiyi kaldir',
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
            const _PageMessage(message: 'Secili hesapta mesaj yok.')
          else
            ...items.map((message) => _MessageCard(message: message)),
        ],
      ),
      error: (error, stackTrace) => _PageMessage(
        message: readableApiError(error, 'Mesajlar alinamadi.'),
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
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message.subject ?? 'Konu yok',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 6),
            Text(message.snippet ?? 'On izleme yok.'),
            const SizedBox(height: 8),
            Wrap(
              spacing: 10,
              runSpacing: 6,
              children: [
                Text(
                  message.fromAddress ?? 'Gonderen yok',
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

String _providerLabel(String provider) {
  return switch (provider) {
    'gmail' => 'Gmail',
    'outlook' => 'Outlook',
    _ => provider,
  };
}

String _formatDateTime(DateTime value) {
  final local = value.toLocal();
  return '${local.day.toString().padLeft(2, '0')}.'
      '${local.month.toString().padLeft(2, '0')} '
      '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}';
}
