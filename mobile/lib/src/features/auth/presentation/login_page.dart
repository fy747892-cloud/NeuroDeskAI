import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/demo_mode.dart';
import '../../../core/widgets/app_components.dart';
import '../../../core/widgets/auth_background.dart';
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
  bool _obscurePassword = true;
  String? _validationMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final authState = ref.watch(authControllerProvider);
    final isLoading = authState.isLoading;
    final hasLockedSession = authState.valueOrNull?.hasLockedSession ?? false;
    final errorMessage =
        _validationMessage ?? authState.valueOrNull?.errorMessage;

    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          const AuthBackdrop(),
          SafeArea(
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                const SizedBox(height: 32),
                Column(
                  children: [
                    Image.asset(
                      'assets/brand/neurodesk_mark.png',
                      width: 88,
                      height: 88,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'NeuroDesk AI',
                      style: theme.textTheme.headlineMedium?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'YAPAY ZEKA DESTEKLİ SATIŞ ASİSTANINIZ',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: theme.colorScheme.secondary,
                        fontWeight: FontWeight.w700,
                        fontSize: 11,
                        letterSpacing: 1.4,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 28),
                AppCard(
                  radius: kLargeCardRadius,
                  padding: const EdgeInsets.all(28),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text('Giriş yap', style: theme.textTheme.headlineMedium),
                      const SizedBox(height: 4),
                      Text(
                        'Devam etmek için bilgilerinizi girin.',
                        style: theme.textTheme.bodyMedium,
                      ),
                      const SizedBox(height: 22),
                      TextField(
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        textInputAction: TextInputAction.next,
                        decoration: const InputDecoration(
                          labelText: 'E-posta',
                          hintText: 'ornek@neurodesk.ai',
                          prefixIcon: Icon(Icons.mail_outline),
                        ),
                      ),
                      const SizedBox(height: 14),
                      TextField(
                        controller: _passwordController,
                        obscureText: _obscurePassword,
                        textInputAction: TextInputAction.done,
                        onSubmitted: (_) => _submit(),
                        decoration: InputDecoration(
                          labelText: 'Şifre',
                          prefixIcon: const Icon(Icons.lock_outline),
                          suffixIcon: IconButton(
                            icon: Icon(_obscurePassword
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined),
                            onPressed: () => setState(
                                () => _obscurePassword = !_obscurePassword),
                          ),
                        ),
                      ),
                      const SizedBox(height: 6),
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
                        controlAffinity: ListTileControlAffinity.leading,
                        contentPadding: EdgeInsets.zero,
                        visualDensity: VisualDensity.compact,
                      ),
                      const SizedBox(height: 10),
                      FilledButton(
                        style: FilledButton.styleFrom(
                          minimumSize: const Size.fromHeight(52),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          shadowColor: theme.colorScheme.primary,
                          elevation: 8,
                        ),
                        onPressed: isLoading ? null : _submit,
                        child:
                            Text(isLoading ? 'Giriş yapılıyor' : 'Giriş yap'),
                      ),
                      if (hasLockedSession || testerLoginEnabled) ...[
                        const SizedBox(height: 18),
                        Row(
                          children: [
                            Expanded(child: Divider(color: theme.colorScheme.outlineVariant)),
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 12),
                              child: Text('veya', style: theme.textTheme.bodySmall),
                            ),
                            Expanded(child: Divider(color: theme.colorScheme.outlineVariant)),
                          ],
                        ),
                        const SizedBox(height: 14),
                      ],
                      if (hasLockedSession)
                        OutlinedButton.icon(
                          onPressed: isLoading
                              ? null
                              : () => ref
                                  .read(authControllerProvider.notifier)
                                  .unlockSavedSession(),
                          icon: const Icon(Icons.fingerprint),
                          label: const Text('Biyometrik ile devam et'),
                        ),
                      if (hasLockedSession && testerLoginEnabled)
                        const SizedBox(height: 10),
                      if (testerLoginEnabled)
                        OutlinedButton.icon(
                          onPressed: isLoading
                              ? null
                              : () => ref
                                  .read(authControllerProvider.notifier)
                                  .loginAsTester(rememberMe: _rememberMe),
                          icon: const Icon(Icons.science_outlined),
                          label: const Text('Tester olarak gir'),
                        ),
                      if (errorMessage != null) ...[
                        const SizedBox(height: 14),
                        Text(
                          errorMessage,
                          style: TextStyle(color: theme.colorScheme.error),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                Center(
                  child: RichText(
                    text: TextSpan(
                      style: theme.textTheme.bodyMedium,
                      children: [
                        const TextSpan(text: 'Hesabınız yok mu? '),
                        TextSpan(
                          text: 'Yeni hesap oluştur',
                          style: TextStyle(
                            color: theme.colorScheme.secondary,
                            fontWeight: FontWeight.w700,
                          ),
                          recognizer: TapGestureRecognizer()
                            ..onTap = isLoading
                                ? null
                                : () => context.go('/auth/register'),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
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
