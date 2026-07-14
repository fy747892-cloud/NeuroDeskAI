import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:neurodesk_ai_mobile/src/app.dart';
import 'package:neurodesk_ai_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:neurodesk_ai_mobile/src/features/auth/domain/auth_tokens.dart';

void main() {
  testWidgets('redirects unauthenticated users to login', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          secureTokenStoreProvider.overrideWithValue(_FakeSecureTokenStore()),
        ],
        child: const NeuroDeskMobileApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('NeuroDesk AI'), findsOneWidget);
    expect(find.text('Giris yap'), findsWidgets);
  });
}

class _FakeSecureTokenStore extends SecureTokenStore {
  _FakeSecureTokenStore() : super(const FlutterSecureStorage());

  @override
  Future<AuthTokens?> read() async => null;

  @override
  Future<void> save(AuthTokens tokens) async {}

  @override
  Future<void> clear() async {}
}
