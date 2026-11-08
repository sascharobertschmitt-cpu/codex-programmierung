-- Solo-Modus: computergesteuerte Gegner (Bots) für "Aal You Ready?"
-- Bots sind normale Mitglieder mit is_bot=true. Ihre Züge führt party_bot_tick aus,
-- das der Client des Hosts regelmäßig aufruft. Alle Regeln laufen über party_action,
-- Bots können also nicht schummeln. Ohne Bots ändert sich am Spiel nichts.

alter table public.party_members add column if not exists is_bot boolean not null default false;

-- Bot zur Lobby hinzufügen (nur Host, nur in der Lobby, max. 8 Mitglieder)
create or replace function public.party_add_bot(p_code text, p_host_token uuid)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare r public.party_rooms; n int; nb int; tok uuid;
  names text[] := array['🤖 DJ Bitrate','🤖 Türsteher-Tron','🤖 Nebelmaschine 3000','🤖 Afterhour-Annette',
                        '🤖 Bassdrop-Bernd','🤖 Strobo-Sabine','🤖 Kickdrum-Kalle'];
begin
  select * into r from public.party_rooms where code = upper(trim(p_code)) for update;
  if not found then raise exception 'Lobby nicht gefunden'; end if;
  if r.host_token is distinct from p_host_token then raise exception 'Nur Host kann Bots hinzufügen'; end if;
  if r.status <> 'lobby' then raise exception 'Spiel läuft bereits'; end if;
  select count(*), count(*) filter (where is_bot) into n, nb from public.party_members where room_id = r.id;
  if n >= 8 then raise exception 'Lobby voll'; end if;
  insert into public.party_members(room_id, name, is_bot) values (r.id, names[nb % array_length(names, 1) + 1], true);
  select token into tok from public.party_members where room_id = r.id order by joined_at, id limit 1;
  return public.party_snapshot(p_code, tok);
end
$function$;

-- Bot wieder entfernen (nur Host, nur Lobby): entfernt den zuletzt hinzugefügten Bot
create or replace function public.party_remove_bot(p_code text, p_host_token uuid)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare r public.party_rooms; tok uuid;
begin
  select * into r from public.party_rooms where code = upper(trim(p_code)) for update;
  if not found then raise exception 'Lobby nicht gefunden'; end if;
  if r.host_token is distinct from p_host_token then raise exception 'Nur Host kann Bots entfernen'; end if;
  if r.status <> 'lobby' then raise exception 'Spiel läuft bereits'; end if;
  delete from public.party_members where id = (select id from public.party_members where room_id = r.id and is_bot
                                               order by joined_at desc, id desc limit 1);
  select token into tok from public.party_members where room_id = r.id order by joined_at, id limit 1;
  return public.party_snapshot(p_code, tok);
end
$function$;

-- Ein Bot-Schritt. Wird vom Host-Client etwa alle 2 s aufgerufen und tut höchstens eine Sache.
create or replace function public.party_bot_tick(p_code text, p_host_token uuid)
returns jsonb
language plpgsql
security definer
set search_path to ''
as $function$
declare r public.party_rooms; n int; act public.party_members; judge public.party_members;
  b record; p record; ans jsonb; term text; cat text; did text := null; host_tok uuid; v_ans text;
begin
  select * into r from public.party_rooms where code = upper(trim(p_code));
  if not found then raise exception 'Lobby nicht gefunden'; end if;
  if r.host_token is distinct from p_host_token then raise exception 'Nur Host steuert Bots'; end if;
  select token into host_tok from public.party_members where room_id = r.id order by joined_at, id limit 1;
  if r.status <> 'playing' or not exists (select 1 from public.party_members where room_id = r.id and is_bot) then
    return jsonb_build_object('did', null);
  end if;
  select count(*) into n from public.party_members where room_id = r.id;
  select * into act from public.party_members where room_id = r.id order by joined_at, id offset (r.turn_index % n) limit 1;
  select * into judge from public.party_members where room_id = r.id order by joined_at, id offset ((r.turn_index + 1) % n) limit 1;

  if r.phase = 'ready' and act.is_bot then
    perform public.party_action(p_code, act.token, null, 'roll');
    did := 'roll';

  elsif r.phase = 'event' and act.is_bot then
    perform public.party_action(p_code, act.token, null, 'event_next');
    did := 'event_next';

  elsif r.phase = 'task' and act.is_bot then
    -- Bots können keine Pantomime. Ergebnis wird ausgewürfelt (60 %) und als Ereignis angezeigt.
    if random() < 0.6 then
      update public.party_members set points = points + 1 where id = act.id;
      update public.party_rooms set phase = 'event', timer_started_at = null,
        task = act.name || ' hat die Aufgabe gemeistert! +1 Punkt' where id = r.id;
    else
      update public.party_rooms set phase = 'event', timer_started_at = null,
        task = act.name || ' ist an der Aufgabe gescheitert.' where id = r.id;
    end if;
    did := 'task';

  elsif r.phase = 'slf' then
    -- Jeder Bot legt einmal einen Entwurf ab (gilt bei Rundenende als Abgabe)
    for b in select * from public.party_members m where m.room_id = r.id and m.is_bot
             and not exists (select 1 from public.party_slf_answers a where a.room_id = r.id
                             and a.turn_index = r.turn_index and a.player_id = m.id) loop
      ans := '{}'::jsonb;
      foreach cat in array array['Stadt','Land','Fluss','Tier','Beruf'] loop
        term := null;
        if random() < 0.75 then
          select initcap(l.term) into term from public.party_slf_lexicon l
          where l.category = cat and upper(left(l.term, 1)) = r.slf_letter order by random() limit 1;
        end if;
        ans := ans || jsonb_build_object(cat, coalesce(term, ''));
      end loop;
      perform public.party_slf_draft(p_code, b.token, ans);
      did := 'slf_draft';
    end loop;
    -- Nur Bots im Spiel? Dann Runde sofort beenden.
    if did is null and not exists (select 1 from public.party_members where room_id = r.id and not is_bot) then
      perform public.party_action(p_code, act.token, null, 'slf_stop');
      did := 'slf_stop';
    end if;

  elsif r.phase = 'slf_review' then
    -- Bots bewerten alle prüfbaren fremden Antworten (Lexikon = ja, sonst meistens nein)
    for b in select * from public.party_members m where m.room_id = r.id and m.is_bot loop
      for p in select a.player_id, k.key cat, k.value val from public.party_slf_answers a
               cross join lateral jsonb_each_text(a.answers) k
               where a.room_id = r.id and a.turn_index = r.turn_index and a.player_id <> b.id
                 and trim(k.value) <> '' and upper(left(trim(k.value), 1)) = r.slf_letter
                 and not exists (select 1 from public.party_slf_votes v where v.room_id = r.id and v.turn_index = r.turn_index
                                 and v.player_id = a.player_id and v.category = k.key and v.reviewer_id = b.id) loop
        begin
          perform public.party_slf_vote(p_code, b.token, p.player_id, p.cat,
                                        public.party_slf_valid(p.cat, p.val, r.slf_letter) or random() < 0.35);
          did := 'slf_vote';
        exception when others then null;
        end;
      end loop;
    end loop;

  elsif r.phase = 'slf_results' and act.is_bot then
    perform public.party_action(p_code, act.token, null, 'slf_next');
    did := 'slf_next';
  end if;

  return jsonb_build_object('did', did, 'snapshot', public.party_snapshot(p_code, host_tok));
end
$function$;

revoke all on function public.party_add_bot(text, uuid) from public;
revoke all on function public.party_remove_bot(text, uuid) from public;
revoke all on function public.party_bot_tick(text, uuid) from public;
grant execute on function public.party_add_bot(text, uuid) to anon, authenticated;
grant execute on function public.party_remove_bot(text, uuid) to anon, authenticated;
grant execute on function public.party_bot_tick(text, uuid) to anon, authenticated;

-- party_action: Ist der Bewerter ein Bot, darf der aktive Mensch seine Aufgabe selbst bewerten.
do $migration$
declare def text; new_def text;
begin
  def := pg_get_functiondef('public.party_action(text,uuid,uuid,text)'::regprocedure);
  new_def := replace(def,
$a$if idx<>judge_idx then raise exception 'Nur der andere Spieler darf bewerten'; end if;$a$,
$b$if idx<>judge_idx and not (idx=(r.turn_index%n) and coalesce((select pm.is_bot from public.party_members pm where pm.room_id=r.id order by pm.joined_at,pm.id offset judge_idx limit 1),false)) then raise exception 'Nur der andere Spieler darf bewerten'; end if;$b$);
  if new_def = def then raise exception 'Migration: Bewertungszweig nicht gefunden'; end if;
  execute new_def;
end
$migration$;

-- party_snapshot: is_bot pro Spieler; you_judge auch für den aktiven Menschen, wenn der Bewerter ein Bot ist
do $migration$
declare def text; new_def text;
begin
  def := pg_get_functiondef('public.party_snapshot(text,uuid)'::regprocedure);
  new_def := replace(def, $a$'lap',lap,'cash',cash,'skip',skip)$a$, $b$'lap',lap,'cash',cash,'skip',skip,'is_bot',is_bot)$b$);
  if new_def = def then raise exception 'Migration: Spielerliste nicht gefunden'; end if;
  def := new_def;
  new_def := replace(def, $a$'you_judge',m.id=judge_player,$a$,
    $b$'you_judge',(m.id=judge_player or (m.id=active_player and coalesce((select pm.is_bot from public.party_members pm where pm.id=judge_player),false))),'judge_is_bot',coalesce((select pm.is_bot from public.party_members pm where pm.id=judge_player),false),$b$);
  if new_def = def then raise exception 'Migration: you_judge nicht gefunden'; end if;
  execute new_def;
end
$migration$;
