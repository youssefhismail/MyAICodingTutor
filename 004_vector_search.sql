-- Migration: create vector search RPC for RAG Phase 3
-- Run this in your Supabase SQL Editor

-- Create a function to perform cosine distance vector search over document_chunks,
-- isolated to a specific session_id.
drop function if exists public.match_document_chunks;

create or replace function public.match_document_chunks (
  query_embedding vector(3072),
  match_count int,
  p_session_id uuid
)
returns table (
  chunk_id uuid,
  document_id uuid,
  filename text,
  sequence_number integer,
  start_offset integer,
  end_offset integer,
  content text,
  distance float
)
language plpgsql
as $$
begin
  return query
  select
    c.id as chunk_id,
    c.document_id,
    d.filename,
    c.sequence_number,
    c.start_offset,
    c.end_offset,
    c.content,
    (c.embedding <=> query_embedding) as distance
  from public.document_chunks c
  inner join public.documents d on c.document_id = d.id
  where d.session_id = p_session_id
  order by c.embedding <=> query_embedding asc
  limit match_count;
end;
$$;
