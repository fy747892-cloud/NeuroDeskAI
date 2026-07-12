import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/appointments/presentation/appointments_page.dart';
import '../features/auth/presentation/auth_controller.dart';
import '../features/auth/presentation/login_page.dart';
import '../features/dashboard/presentation/dashboard_page.dart';
import '../features/shell/mobile_shell.dart';
import '../features/tasks/presentation/tasks_page.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authControllerProvider);

  return GoRouter(
    initialLocation: '/app/dashboard',
    redirect: (context, state) {
      final isLoggedIn = authState.valueOrNull?.isAuthenticated ?? false;
      final isAuthRoute = state.uri.path.startsWith('/auth');

      if (!isLoggedIn && !isAuthRoute) {
        return '/auth/login';
      }
      if (isLoggedIn && isAuthRoute) {
        return '/app/dashboard';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/auth/login',
        builder: (context, state) => const LoginPage(),
      ),
      ShellRoute(
        builder: (context, state, child) => MobileShell(child: child),
        routes: [
          GoRoute(
            path: '/app/dashboard',
            builder: (context, state) => const DashboardPage(),
          ),
          GoRoute(
            path: '/app/tasks',
            builder: (context, state) => const TasksPage(),
          ),
          GoRoute(
            path: '/app/appointments',
            builder: (context, state) => const AppointmentsPage(),
          ),
        ],
      ),
    ],
  );
});
