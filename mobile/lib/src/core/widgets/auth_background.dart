import 'dart:ui';

import 'package:flutter/material.dart';

/// Soft blurred primary/secondary "blob" backdrop matching the Stitch
/// login/register mockups -- a light, airy alternative to the app's old
/// full-bleed dark gradient auth screens.
class AuthBackdrop extends StatelessWidget {
  const AuthBackdrop({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Positioned.fill(
      child: ImageFiltered(
        imageFilter: ImageFilter.blur(sigmaX: 80, sigmaY: 80),
        child: Stack(
          children: [
            Positioned(
              top: -80,
              left: -80,
              child: _Blob(size: 260, color: theme.colorScheme.primary),
            ),
            Positioned(
              bottom: -100,
              right: -100,
              child: _Blob(size: 300, color: theme.colorScheme.secondary),
            ),
          ],
        ),
      ),
    );
  }
}

class _Blob extends StatelessWidget {
  const _Blob({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color.withValues(alpha: 0.3),
      ),
    );
  }
}
