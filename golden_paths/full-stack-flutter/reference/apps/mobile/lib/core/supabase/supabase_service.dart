import 'package:supabase_flutter/supabase_flutter.dart';

/// Convenience accessor for the Supabase client.
///
/// The client is initialized once in main.dart via Supabase.initialize().
/// supabase_flutter automatically persists the session using flutter_secure_storage.
abstract final class SupabaseService {
  static SupabaseClient get client => Supabase.instance.client;

  static User? get currentUser => client.auth.currentUser;

  static Session? get currentSession => client.auth.currentSession;

  static bool get isAuthenticated => currentUser != null;

  static Stream<AuthState> get authStateChanges => client.auth.onAuthStateChange;

  static Future<AuthResponse> signInWithEmail({
    required String email,
    required String password,
  }) async {
    return client.auth.signInWithPassword(email: email, password: password);
  }

  static Future<OAuthResponse> signInWithGoogle() async {
    return client.auth.signInWithOAuth(OAuthProvider.google);
  }

  static Future<void> signOut() async {
    await client.auth.signOut();
  }
}
