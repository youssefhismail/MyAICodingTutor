-- Drop the old messages table before running this migration.
-- WARNING: this destroys existing conversation data.
--
--   DROP TABLE IF EXISTS public.messages CASCADE;

create table if not exists public.messages (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    sequence integer not null,
    created_at timestamptz not null default now(),

    unique (session_id, sequence)
);

create index if not exists idx_messages_session_sequence
    on public.messages(session_id, sequence);

alter table public.messages enable row level security;

drop policy if exists "messages_select_all" on public.messages;
create policy "messages_select_all"
on public.messages
for select
to public
using (true);

drop policy if exists "messages_insert_all" on public.messages;
create policy "messages_insert_all"
on public.messages
for insert
to public
with check (true);

drop policy if exists "messages_delete_session" on public.messages;
create policy "messages_delete_session"
on public.messages
for delete
to public
using (true);

-- Atomically insert a user + assistant message pair with consecutive
-- sequence numbers.
--
-- pg_advisory_xact_lock serialises concurrent calls for the same
-- session_id so two transactions never read the same MAX(sequence).
-- The lock is released automatically when the transaction commits.
-- The UNIQUE(session_id, sequence) constraint acts as a safety net
-- in case the advisory lock is bypassed (e.g. direct SQL inserts).

create or replace function save_exchange(
    p_session_id uuid,
    p_user_content text,
    p_assistant_content text
) returns setof public.messages
language plpgsql as $$
declare
    next_seq int;
begin
    -- Serialise concurrent calls for the same session.
    perform pg_advisory_xact_lock(hashtext(p_session_id::text));

    select coalesce(max(sequence), -1) + 1
      into next_seq
      from public.messages
     where session_id = p_session_id;

    insert into public.messages (session_id, role, content, sequence)
    values (p_session_id, 'user', p_user_content, next_seq);

    insert into public.messages (session_id, role, content, sequence)
    values (p_session_id, 'assistant', p_assistant_content, next_seq + 1);

    return query
        select * from public.messages
         where session_id = p_session_id
           and sequence in (next_seq, next_seq + 1);
end;
$$;