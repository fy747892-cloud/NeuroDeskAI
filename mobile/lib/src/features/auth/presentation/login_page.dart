import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/demo_mode.dart';
import 'auth_controller.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _rememberMe = true;
  String? _validationMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    final isLoading = authState.isLoading;
    final hasLockedSession = authState.valueOrNull?.hasLockedSession ?? false;
    final errorMessage =
        _validationMessage ?? authState.valueOrNull?.errorMessage;

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF150C3C), Color(0xFF241169), Color(0xFF3525CD)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              const SizedBox(height: 48),
              const _AuthBrand(),
              const SizedBox(height: 28),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Giriş yap',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'Mobil çalışma alanına devam et.',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      const SizedBox(height: 18),
                      TextField(
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        textInputAction: TextInputAction.next,
                        decoration: const InputDecoration(labelText: 'E-posta'),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _passwordController,
                        obscureText: true,
                        onSubmitted: (_) => _submit(),
                        decoration: const InputDecoration(labelText: 'Şifre'),
                      ),
                      const SizedBox(height: 8),
                      CheckboxListTile(
                        value: _rememberMe,
                        onChanged: isLoading
                            ? null
                            : (value) {
                                setState(() {
                                  _rememberMe = value ?? true;
                                });
                              },
                        title: const Text('Beni hatırla'),
                        subtitle: const Text('Oturumu bu cihazda sakla'),
                        controlAffinity: ListTileControlAffinity.leading,
                        contentPadding: EdgeInsets.zero,
                        visualDensity: VisualDensity.compact,
                      ),
                      const SizedBox(height: 16),
                      FilledButton(
                        onPressed: isLoading ? null : _submit,
                        child:
                            Text(isLoading ? 'Giriş yapılıyor' : 'Giriş yap'),
                      ),
                      if (hasLockedSession) ...[
                        const SizedBox(height: 10),
                        OutlinedButton.icon(
                          onPressed: isLoading
                              ? null
                              : () => ref
                                  .read(authControllerProvider.notifier)
                                  .unlockSavedSession(),
                          icon: const Icon(Icons.fingerprint),
                          label: const Text('Biyometrik ile devam et'),
                        ),
                      ],
                      if (testerLoginEnabled) ...[
                        const SizedBox(height: 10),
                        OutlinedButton.icon(
                          onPressed: isLoading
                              ? null
                              : () => ref
                                  .read(authControllerProvider.notifier)
                                  .loginAsTester(rememberMe: _rememberMe),
                          icon: const Icon(Icons.science_outlined),
                          label: const Text('Tester olarak gir'),
                        ),
                      ],
                      const SizedBox(height: 10),
                      TextButton(
                        onPressed: isLoading
                            ? null
                            : () => context.go('/auth/register'),
                        child: const Text('Yeni hesap oluştur'),
                      ),
                      if (errorMessage != null) ...[
                        const SizedBox(height: 12),
                        Text(
                          errorMessage,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.error,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _submit() {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      setState(() {
        _validationMessage = 'E-posta ve şifre zorunlu.';
      });
      return;
    }

    setState(() => _validationMessage = null);
    ref.read(authControllerProvider.notifier).login(
          email,
          password,
          rememberMe: _rememberMe,
        );
  }
}

class _AuthBrand extends StatelessWidget {
  const _AuthBrand();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(14),
              child: Image.asset(
                'assets/brand/neurodesk_mark.png',
                width: 58,
                height: 58,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 14),
            const Text(
              'NeuroDesk AI',
              style: TextStyle(
                color: Colors.white,
                fontSize: 32,
                fontWeight: FontWeight.w900,
                height: 1.05,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        const Text(
          'AI destekli operasyon alanin cebinde.',
          style: TextStyle(
            color: Color(0xFFC3C0FF),
            fontSize: 16,
            height: 1.35,
          ),
        ),
      ],
    );
  }
}
