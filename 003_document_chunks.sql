-- Migration: create the document_chunks table for RAG Phase 1
-- Run this in your Supabase SQL Editor after supabase.sql and supabase_documents.sql

create table if not exists public.document_chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references public.documents(id) on delete cascade,
    sequence_number integer not null,
    start_offset integer not null,
    end_offset integer not null,
    content text not null,
    created_at timestamptz not null default now(),

    -- Enforce uniqueness to prevent duplicate sequence numbers per document
    unique (document_id, sequence_number)
);

-- Optimize sequential retrieval of chunks for a specific document
create index if not exists idx_document_chunks_document_seq
    on public.document_chunks(document_id, sequence_number);

alter table public.document_chunks enable row level security;

drop policy if exists "document_chunks_select_all" on public.document_chunks;
create policy "document_chunks_select_all"
on public.document_chunks
for select
to public
using (true);

drop policy if exists "document_chunks_insert_all" on public.document_chunks;
create policy "document_chunks_insert_all"
on public.document_chunks
for insert
to public
with check (true);

drop policy if exists "document_chunks_delete_session" on public.document_chunks;
create policy "document_chunks_delete_session"
on public.document_chunks
for delete
to public
using (true);
