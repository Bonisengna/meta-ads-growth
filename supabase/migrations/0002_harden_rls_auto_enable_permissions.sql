-- Fase 2 — endurecimento de permissões de função existente no projeto Supabase.
-- A função public.rls_auto_enable() já existia no projeto e foi sinalizada pelo advisor
-- porque anon/authenticated podiam executá-la. O backend não precisa expor essa RPC.

revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
