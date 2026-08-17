import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

export const isSupabaseConfigured = Boolean(url && publishableKey);

export function getSupabaseBrowserClient() {
  return createClient(
    url ?? "http://127.0.0.1:54321",
    publishableKey ?? "frontend-not-configured",
  );
}
