-- Kopfbedeckung pro Spieler: in der Lobby wählbar, unterscheidet die Figuren im Rundkurs.
alter table public.party_members add column if not exists hat text;

create or replace function public.party_hat_list()
returns text[] language sql immutable set search_path to '' as
$$ select array['fischerhut','cap','kopfhoerer','beanie','gasmaske','aalmuetze','hasenohren','ledhelm'] $$;

-- Neue Mitglieder (auch Bots) bekommen eine noch freie Kopfbedeckung
create or replace function public.party_member_default_hat()
returns trigger language plpgsql security definer set search_path to '' as $$
begin
  if new.hat is null then
    select h into new.hat from unnest(public.party_hat_list()) h
      where h not in (select coalesce(m.hat, '') from public.party_members m where m.room_id = new.room_id)
      order by random() limit 1;
    if new.hat is null then new.hat := (public.party_hat_list())[floor(random() * 8)::int + 1]; end if;
  end if;
  return new;
end $$;
drop trigger if exists party_member_default_hat on public.party_members;
create trigger party_member_default_hat before insert on public.party_members
  for each row execute function public.party_member_default_hat();

update public.party_members set hat = (public.party_hat_list())[floor(random() * 8)::int + 1] where hat is null;

create or replace function public.party_set_hat(p_code text, p_token uuid, p_hat text)
returns jsonb language plpgsql security definer set search_path to '' as $$
declare r public.party_rooms; m public.party_members;
begin
  select * into r from public.party_rooms where code = upper(trim(p_code));
  if not found then raise exception 'Lobby nicht gefunden'; end if;
  select * into m from public.party_members where room_id = r.id and token = p_token;
  if not found then raise exception 'Kein Zugang'; end if;
  if r.status <> 'lobby' then raise exception 'Kopfbedeckung nur vor dem Start wählbar'; end if;
  if not (p_hat = any(public.party_hat_list())) then raise exception 'Unbekannte Kopfbedeckung'; end if;
  update public.party_members set hat = p_hat where id = m.id;
  return public.party_snapshot(p_code, p_token);
end $$;
revoke all on function public.party_set_hat(text, uuid, text) from public;
grant execute on function public.party_set_hat(text, uuid, text) to anon, authenticated;

do $migration$
declare def text; new_def text;
begin
  def := pg_get_functiondef('public.party_snapshot(text,uuid)'::regprocedure);
  new_def := replace(def, $a$'skip',skip,'is_bot',is_bot)$a$, $b$'skip',skip,'is_bot',is_bot,'hat',hat)$b$);
  if new_def = def then raise exception 'Migration: Spielerliste im Snapshot nicht gefunden'; end if;
  execute new_def;
end
$migration$;
