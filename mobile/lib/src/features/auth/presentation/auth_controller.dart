import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_error.dart';
import '../data/auth_repository.dart';
import '../data/secure_token_store.dart';
import '../domain/auth_tokens.dart';

final authControllerProvider =
    AsyncNotifierProvider<AuthController, AuthState>(AuthController.new);

class AuthState {
  const AuthState({required this.tokens, this.errorMessage});

  final AuthTokens? tokens;
  final String? errorMessage;

  bool get isAuthenticated => tokens != null;

  AuthState copyWith({AuthTokens? tokens, String? errorMessage}) {
    return AuthState(
      tokens: tokens ?? this.tokens,
      errorMessage: errorMessage,
    );
  }
}

class AuthController extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    final tokens = await ref.watch(secureTokenStoreProvider).read();
    return AuthState(tokens: tokens);
  }

  Future<void> login(String email, String password) async {
    state = const AsyncLoading();
    try {
      final tokens = await ref
          .read(authRepositoryProvider)
          .login(email: email, password: password);
      await ref.read(secureTokenStoreProvider).save(tokens);
      state = AsyncData(AuthState(tokens: tokens));
    } catch (error) {
      state = AsyncData(
        AuthState(
          tokens: null,
          errorMessage: readableApiError(error, 'Giris tamamlanamadi.'),
        ),
      );
    }
  }

  Future<void> logout() async {
    final tokens = state.valueOrNull?.tokens;
    await ref.read(secureTokenStoreProvider).clear();
    state = const AsyncData(AuthState(tokens: null));
    if (tokens != null) {
      await ref.read(authRepositoryProvider).logout(tokens.refreshToken);
    }
  }
}
