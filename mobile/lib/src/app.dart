import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router.dart';
import 'core/theme.dart';

class NeuroDeskMobileApp extends ConsumerWidget {
  const NeuroDeskMobileApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      routerConfig: router,
      theme: buildNeuroDeskTheme(),
      title: 'NeuroDesk AI',
    );
  }
}
