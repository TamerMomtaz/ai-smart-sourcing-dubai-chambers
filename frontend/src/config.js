export const config = {
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL,
  supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY,
  apiUrl: import.meta.env.VITE_API_URL || ''
};

if (!config.supabaseUrl || !config.supabaseAnonKey) {
  console.error('Missing Supabase environment variables');
}