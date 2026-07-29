import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// Exact design tokens from the NeuroDesk AI Stitch project
// (projectId 3678649583756480882) -- the same token block appears verbatim
// in the tailwind config of every generated screen (Özet, Daha Fazla,
// Fırsatlar, Kişiler, Ayarlar, Görüşmeler, Ses Kaydı, Takvim, ...). Do not
// approximate these with different hex values.
const _primary = Color(0xFF1E00A9);
const _primaryContainer = Color(0xFF3525CD);
const _secondary = Color(0xFF4430E5);
const _secondaryContainer = Color(0xFF5D50FE);
const _onBackground = Color(0xFF1B1B24);
const _outline = Color(0xFF777587);
const _outlineVariant = Color(0xFFC7C4D8);
const _surface = Color(0xFFFFFFFF);
const _surfaceContainer = Color(0xFFF0ECF9);
const _surfaceContainerHigh = Color(0xFFEAE6F4);
const _surfaceContainerHighest = Color(0xFFE4E1EE);
const _error = Color(0xFFBA1A1A);
// Literal <body> background override used on every Stitch screen -- distinct
// from the "surface"/"background" tailwind token (#FCF8FF) used for fixed
// headers.
const _pageBackground = Color(0xFFF4F5FB);
const _primarySoft = Color(0x1A3525CD);

ThemeData buildNeuroDeskTheme() {
  final baseTextTheme = GoogleFonts.plusJakartaSansTextTheme();

  return ThemeData(
    colorScheme: const ColorScheme.light(
      primary: _primary,
      primaryContainer: _primaryContainer,
      secondary: _secondary,
      secondaryContainer: _secondaryContainer,
      tertiary: Color(0xFF2C3141),
      error: _error,
      surface: _surface,
      onSurface: _onBackground,
      onPrimary: Colors.white,
      onSecondary: Colors.white,
      surfaceContainer: _surfaceContainer,
      surfaceContainerHigh: _surfaceContainerHigh,
      surfaceContainerHighest: _surfaceContainerHighest,
      outline: _outline,
      outlineVariant: _outlineVariant,
    ),
    scaffoldBackgroundColor: _pageBackground,
    useMaterial3: true,
    fontFamily: baseTextTheme.bodyMedium?.fontFamily,
    appBarTheme: AppBarTheme(
      centerTitle: false,
      elevation: 0,
      backgroundColor: _surface,
      foregroundColor: _onBackground,
      surfaceTintColor: Colors.transparent,
      titleTextStyle: GoogleFonts.plusJakartaSans(
        color: _onBackground,
        fontSize: 18,
        fontWeight: FontWeight.w700,
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: _surface,
      indicatorColor: _primarySoft,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => GoogleFonts.plusJakartaSans(
          color: states.contains(WidgetState.selected) ? _secondary : _outline,
          fontSize: 11,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w700
              : FontWeight.w500,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected) ? _secondary : _outline,
          size: 22,
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: const OutlineInputBorder(),
      filled: true,
      fillColor: _surfaceContainer.withValues(alpha: 0.4),
      focusedBorder: const OutlineInputBorder(
        borderSide: BorderSide(color: _primary, width: 1.4),
      ),
      enabledBorder: const OutlineInputBorder(
        borderSide: BorderSide(color: _outlineVariant),
      ),
    ),
    cardTheme: CardThemeData(
      color: _surface,
      margin: EdgeInsets.zero,
      elevation: 0,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: _outlineVariant),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: _primary,
        foregroundColor: Colors.white,
        textStyle: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w800),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        minimumSize: const Size(0, 44),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: _onBackground,
        side: const BorderSide(color: _outlineVariant),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        minimumSize: const Size(0, 44),
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: _primarySoft,
      labelStyle: GoogleFonts.plusJakartaSans(
        color: _primary,
        fontWeight: FontWeight.w700,
      ),
      side: BorderSide.none,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
    ),
    textTheme: baseTextTheme.copyWith(
      headlineMedium: GoogleFonts.plusJakartaSans(
        color: _onBackground,
        fontSize: 24,
        fontWeight: FontWeight.w800,
        height: 1.15,
      ),
      titleLarge: GoogleFonts.plusJakartaSans(
        color: _onBackground,
        fontSize: 20,
        fontWeight: FontWeight.w800,
      ),
      titleMedium: GoogleFonts.plusJakartaSans(
        color: _onBackground,
        fontSize: 16,
        fontWeight: FontWeight.w700,
      ),
      labelLarge: GoogleFonts.plusJakartaSans(
        color: _outline,
        fontSize: 13,
        fontWeight: FontWeight.w700,
      ),
      bodyMedium: GoogleFonts.plusJakartaSans(color: _onBackground, height: 1.35),
      bodySmall: GoogleFonts.plusJakartaSans(color: _outline, height: 1.35),
    ),
  );
}
