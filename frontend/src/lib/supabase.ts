import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

export const isSupabaseConfigured = Boolean(url && publishableKey);

let browserClient: SupabaseClient | null = null;

export function getSupabaseBrowserClient() {
  browserClient ??= createClient(
    url ?? "http://127.0.0.1:54321",
    publishableKey ?? "frontend-not-configured",
  );
  return browserClient;
}
