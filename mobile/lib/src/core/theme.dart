import 'package:flutter/material.dart';

ThemeData buildNeuroDeskTheme() {
  const ink = Color(0xFF17211B);
  const green = Color(0xFF257A57);
  const surface = Color(0xFFFFFFFF);
  const background = Color(0xFFF7F8F6);

  return ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: green,
      primary: green,
      surface: surface,
      onSurface: ink,
    ),
    scaffoldBackgroundColor: background,
    useMaterial3: true,
    inputDecorationTheme: const InputDecorationTheme(
      border: OutlineInputBorder(),
      filled: true,
      fillColor: surface,
    ),
    cardTheme: CardThemeData(
      color: surface,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    ),
  );
}
