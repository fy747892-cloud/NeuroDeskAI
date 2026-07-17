import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../data/email_repository.dart';

class EmailOAuthReturnPage extends ConsumerStatefulWidget {
  const EmailOAuthReturnPage({
    super.key,
    required this.provider,
    required this.status,
  });

  final String provider;
  final String? status;

  @override
  ConsumerState<EmailOAuthReturnPage> createState() =>
      _EmailOAuthReturnPageState();
}

class _EmailOAuthReturnPageState extends ConsumerState<EmailOAuthReturnPage> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.invalidate(emailAccountsProvider));
  }

  @override
  Widget build(BuildContext context) {
    final isConnected = widget.status == null || widget.status == 'connected';

    return Scaffold(
      appBar: AppBar(title: const Text('E-posta bağlantısı')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Icon(
                isConnected ? Icons.check_circle : Icons.info_outline,
                color: isConnected
                    ? Theme.of(context).colorScheme.primary
                    : Theme.of(context).colorScheme.error,
                size: 52,
              ),
              const SizedBox(height: 16),
              Text(
                isConnected
                    ? '${_providerLabel(widget.provider)} bağlantısı tamamlandı.'
                    : '${_providerLabel(widget.provider)} bağlantısı kontrol edilmeli.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Text(
                'Hesap listesini yenileyip e-posta ekranına dönebilirsin.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const Spacer(),
              FilledButton.icon(
                onPressed: () => context.go('/app/email'),
                icon: const Icon(Icons.mail_outline),
                label: const Text('E-posta ekranına dön'),
              ),
            ],
          ),
        ),
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
