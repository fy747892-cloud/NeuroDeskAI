import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/ai_approvals/presentation/ai_approvals_page.dart';
import '../features/ai_chat/presentation/ai_chat_page.dart';
import '../features/analytics/presentation/analytics_page.dart';
import '../features/appointments/presentation/appointments_page.dart';
import '../features/auth/presentation/auth_controller.dart';
import '../features/auth/presentation/login_page.dart';
import '../features/auth/presentation/register_page.dart';
import '../features/auth/presentation/splash_page.dart';
import '../features/calls/presentation/calls_page.dart';
import '../features/contacts/presentation/contact_detail_page.dart';
import '../features/contacts/presentation/contacts_page.dart';
import '../features/conversations/presentation/conversations_page.dart';
import '../features/dashboard/presentation/dashboard_page.dart';
import '../features/deals/presentation/deals_page.dart';
import '../features/email/presentation/email_page.dart';
import '../features/files/presentation/files_page.dart';
import '../features/notifications/presentation/notifications_page.dart';
import '../features/priority/presentation/priority_page.dart';
import '../features/search/presentation/search_page.dart';
import '../features/settings/presentation/settings_page.dart';
import '../features/shell/mobile_shell.dart';
import '../features/tasks/presentation/tasks_page.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authControllerProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      final isLoadingAuth = authState.isLoading;
      final isLoggedIn = authState.valueOrNull?.isAuthenticated ?? false;
      final isAuthRoute = state.uri.path.startsWith('/auth');
      final isSplashRoute = state.uri.path == '/splash';

      if (isLoadingAuth) {
        return isSplashRoute ? null : '/splash';
      }
      if (isSplashRoute) {
        return isLoggedIn ? '/app/dashboard' : '/auth/login';
      }

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
        path: '/splash',
        builder: (context, state) => const SplashPage(),
      ),
      GoRoute(
        path: '/auth/login',
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: '/auth/register',
        builder: (context, state) => const RegisterPage(),
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
            path: '/app/tasks/:taskId',
            builder: (context, state) => const TasksPage(),
          ),
          GoRoute(
            path: '/app/conversations',
            builder: (context, state) => const ConversationsPage(),
          ),
          GoRoute(
            path: '/app/conversations/:conversationId',
            builder: (context, state) => const ConversationsPage(),
          ),
          GoRoute(
            path: '/app/calls',
            builder: (context, state) => const CallsPage(),
          ),
          GoRoute(
            path: '/app/appointments',
            builder: (context, state) => const AppointmentsPage(),
          ),
          GoRoute(
            path: '/app/appointments/:appointmentId',
            builder: (context, state) => const AppointmentsPage(),
          ),
          GoRoute(
            path: '/app/approvals',
            builder: (context, state) => const AiApprovalsPage(),
          ),
          GoRoute(
            path: '/app/approvals/:approvalId',
            builder: (context, state) => const AiApprovalsPage(),
          ),
          GoRoute(
            path: '/app/chat',
            builder: (context, state) => const AiChatPage(),
          ),
          GoRoute(
            path: '/app/contacts',
            builder: (context, state) => const ContactsPage(),
          ),
          GoRoute(
            path: '/app/contacts/:contactId',
            builder: (context, state) {
              return ContactDetailPage(
                contactId: state.pathParameters['contactId']!,
              );
            },
          ),
          GoRoute(
            path: '/app/search',
            builder: (context, state) => const SearchPage(),
          ),
          GoRoute(
            path: '/app/deals',
            builder: (context, state) => const DealsPage(),
          ),
          GoRoute(
            path: '/app/priority',
            builder: (context, state) => const PriorityPage(),
          ),
          GoRoute(
            path: '/app/analytics',
            builder: (context, state) => const AnalyticsPage(),
          ),
          GoRoute(
            path: '/app/files',
            builder: (context, state) => const FilesPage(),
          ),
          GoRoute(
            path: '/app/files/:fileId',
            builder: (context, state) => const FilesPage(),
          ),
          GoRoute(
            path: '/app/email',
            builder: (context, state) => const EmailPage(),
          ),
          GoRoute(
            path: '/app/settings',
            builder: (context, state) => const SettingsPage(),
          ),
          GoRoute(
            path: '/app/notifications',
            builder: (context, state) => const NotificationsPage(),
          ),
          GoRoute(
            path: '/app/notifications/:notificationId',
            builder: (context, state) => const NotificationsPage(),
          ),
        ],
      ),
    ],
  );
});
