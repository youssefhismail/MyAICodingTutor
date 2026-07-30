-- Migration: create the documents table for uploaded file storage.
-- Run this in your Supabase SQL Editor after the initial supabase.sql migration.
--
-- Future RAG extension:
--   ALTER TABLE public.documents ADD COLUMN embedding vector(1536);
--   CREATE INDEX idx_documents_embedding ON public.documents
--       USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

create table if not exists public.documents (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null,
    filename text not null,
    content text not null,
    uploaded_at timestamptz not null default now()
);

create index if not exists idx_documents_session_id
    on public.documents(session_id);

alter table public.documents enable row level security;

drop policy if exists "documents_select_all" on public.documents;
create policy "documents_select_all"
on public.documents
for select
to public
using (true);

drop policy if exists "documents_insert_all" on public.documents;
create policy "documents_insert_all"
on public.documents
for insert
to public
with check (true);

drop policy if exists "documents_delete_session" on public.documents;
create policy "documents_delete_session"
on public.documents
for delete
to public
using (true);
