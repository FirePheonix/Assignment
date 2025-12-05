// Mock Supabase client
export const createClient = () => ({
  auth: {
    signOut: async () => ({ error: null }),
    getSession: async () => ({ data: { session: null }, error: null }),
    signInWithOAuth: async () => ({ data: null, error: null }),
  },
});
