import 'package:flutter/material.dart';

/// Design token constants mirroring packages/ui-primitives/src/tokens/colors.ts.
///
/// These are raw color values used to build the app's ThemeData.
/// In widgets, always use Theme.of(context).colorScheme — never reference
/// ColorTokens directly in build methods.
abstract final class ColorTokens {
  // Brand
  static const Color primary = Color(0xFF3B82F6); // hsl(221 83% 53%)
  static const Color primaryForeground = Color(0xFFFFFFFF);
  static const Color secondary = Color(0xFF6366F1); // hsl(239 84% 67%)
  static const Color secondaryForeground = Color(0xFFFFFFFF);

  // Semantic — Light
  static const Color background = Color(0xFFFFFFFF);
  static const Color foreground = Color(0xFF0A0A0A);
  static const Color card = Color(0xFFFFFFFF);
  static const Color cardForeground = Color(0xFF0A0A0A);
  static const Color muted = Color(0xFFF1F5F9);
  static const Color mutedForeground = Color(0xFF64748B);
  static const Color border = Color(0xFFE2E8F0);
  static const Color input = Color(0xFFE2E8F0);
  static const Color ring = Color(0xFF3B82F6);

  // Semantic — Dark
  static const Color backgroundDark = Color(0xFF0F172A);
  static const Color foregroundDark = Color(0xFFF8FAFC);
  static const Color cardDark = Color(0xFF1E293B);
  static const Color cardForegroundDark = Color(0xFFF8FAFC);
  static const Color mutedDark = Color(0xFF1E293B);
  static const Color mutedForegroundDark = Color(0xFF94A3B8);
  static const Color borderDark = Color(0xFF334155);

  // Status
  static const Color success = Color(0xFF22C55E);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error = Color(0xFFEF4444);
  static const Color info = Color(0xFF3B82F6);
}
