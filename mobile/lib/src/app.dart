import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/l10n/app_language.dart';
import 'core/router.dart';
import 'core/theme.dart';

class NeuroDeskMobileApp extends ConsumerWidget {
  const NeuroDeskMobileApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final language = ref.watch(appLanguageProvider);

    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      locale: language.locale,
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      routerConfig: router,
      supportedLocales: AppLanguage.values.map((language) => language.locale),
      theme: buildNeuroDeskTheme(),
      title: 'NeuroDesk AI',
    );
  }
}
