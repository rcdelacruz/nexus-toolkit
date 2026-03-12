import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../core/supabase/supabase_service.dart';

part 'auth_provider.g.dart';

@riverpod
class AuthNotifier extends _$AuthNotifier {
  @override
  Future<User?> build() async {
    // Listen for auth state changes and rebuild automatically
    ref.onDispose(
      SupabaseService.authStateChanges.listen((data) {
        state = AsyncData(data.session?.user);
      }).cancel,
    );

    return SupabaseService.currentUser;
  }

  Future<void> signInWithEmail({
    required String email,
    required String password,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final response = await SupabaseService.signInWithEmail(
        email: email,
        password: password,
      );
      return response.user;
    });
  }

  Future<void> signInWithGoogle() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      await SupabaseService.signInWithGoogle();
      return SupabaseService.currentUser;
    });
  }

  Future<void> signOut() async {
    state = const AsyncLoading();
    await SupabaseService.signOut();
    state = const AsyncData(null);
  }
}
