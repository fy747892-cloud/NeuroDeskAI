import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:neurodesk_ai_mobile/src/app.dart';

void main() {
  testWidgets('renders mobile app shell', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: NeuroDeskMobileApp()));
    await tester.pump();

    expect(find.text('NeuroDesk AI'), findsOneWidget);
  });
}
