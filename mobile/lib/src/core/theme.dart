import 'package:flutter/material.dart';

ThemeData buildNeuroDeskTheme() {
  const ink = Color(0xFF17152F);
  const muted = Color(0xFF6B6F82);
  const primary = Color(0xFF3525CD);
  const primarySoft = Color(0x1A3525CD);
  const surface = Color(0xFFFFFFFF);
  const surfaceStrong = Color(0xFFF8F7FF);
  const background = Color(0xFFF4F5FB);
  const line = Color(0xFFE5E7F1);

  return ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: primary,
      primary: primary,
      secondary: const Color(0xFF8B5CF6),
      tertiary: const Color(0xFF4B6BFB),
      error: const Color(0xFFDC6465),
      surface: surface,
      onSurface: ink,
      surfaceContainerHighest: surfaceStrong,
      outline: line,
    ),
    scaffoldBackgroundColor: background,
    useMaterial3: true,
    appBarTheme: const AppBarTheme(
      centerTitle: false,
      elevation: 0,
      backgroundColor: surface,
      foregroundColor: ink,
      surfaceTintColor: Colors.transparent,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: surface,
      indicatorColor: primarySoft,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          color: states.contains(WidgetState.selected) ? primary : muted,
          fontSize: 11,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w700
              : FontWeight.w500,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected) ? primary : muted,
          size: 22,
        ),
      ),
    ),
    inputDecorationTheme: const InputDecorationTheme(
      border: OutlineInputBorder(),
      filled: true,
      fillColor: Color(0xFFFBFBFF),
      focusedBorder: OutlineInputBorder(
        borderSide: BorderSide(color: primary, width: 1.4),
      ),
      enabledBorder: OutlineInputBorder(
        borderSide: BorderSide(color: line),
      ),
    ),
    cardTheme: CardThemeData(
      color: surface,
      margin: EdgeInsets.zero,
      elevation: 0,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: line),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: primary,
        foregroundColor: Colors.white,
        textStyle: const TextStyle(fontWeight: FontWeight.w800),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        minimumSize: const Size(0, 44),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: ink,
        side: const BorderSide(color: line),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        minimumSize: const Size(0, 44),
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: primarySoft,
      labelStyle: const TextStyle(color: primary, fontWeight: FontWeight.w700),
      side: BorderSide.none,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
    ),
    textTheme: const TextTheme(
      headlineMedium: TextStyle(
        color: ink,
        fontSize: 24,
        fontWeight: FontWeight.w800,
        height: 1.15,
      ),
      titleLarge:
          TextStyle(color: ink, fontSize: 20, fontWeight: FontWeight.w800),
      titleMedium:
          TextStyle(color: ink, fontSize: 16, fontWeight: FontWeight.w700),
      labelLarge:
          TextStyle(color: muted, fontSize: 13, fontWeight: FontWeight.w700),
      bodyMedium: TextStyle(color: ink, height: 1.35),
      bodySmall: TextStyle(color: muted, height: 1.35),
    ),
  );
}
