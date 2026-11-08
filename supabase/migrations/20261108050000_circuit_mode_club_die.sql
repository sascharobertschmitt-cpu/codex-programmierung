-- Rundkurs-Modus mit Club-Würfel für "Aal You Ready?"
-- Rückwärtskompatibel: bestehende Lobbys bleiben board_mode='classic' und laufen unverändert.
-- Rundkurs nur, wenn der Host mit p_action='start_circuit' (2 Runden) bzw. 'start_circuit_3' startet.

alter table public.party_rooms
  add column if not exists board_mode text not null default 'classic',
  add column if not exists laps integer not null default 2,
  add column if not exists roll_info jsonb;

alter table public.party_members
  add column if not exists lap integer not null default 0,
  add column if not exists cash integer not null default 0,
  add column if not exists skip boolean not null default false;

-- Ein Wurf im Rundkurs: W6 + Club-Würfel, Runden, Einlass-Karte, Aussetzen, Feldfunktionen.
create or replace function public.party_circuit_roll(p_room uuid, p_member uuid)
returns void
language plpgsql
security definer
set search_path to ''
as $function$
declare
  r public.party_rooms; m public.party_members;
  faces text[] := array['0','2','3','5','7','×2'];
  white int; f int; total int; raw int; gained int; newpos int; newlap int;
  club_name text; gate text := null; effect int; target int; event_text text; info jsonb;
  acts int[] := array[2,4,6,9,11,13,16,18,20,22,25,27,30,33,35,37,39,42,44,46,48,51,53,55,57,59,61,62,63];
  tasks text[] := array['🎭 Stelle einen DJ mit kaputtem Mischpult pantomimisch dar.','🎭 Erkläre Afterhour ohne Morgen, Party oder Feiern.','🎭 Zeichne einen Plattenspieler, ohne zu sprechen.','🎭 Stelle einen Türsteher pantomimisch dar.','🎭 Erkläre Nebelmaschine ohne Nebel, Rauch oder Maschine.','🎭 Zeichne ein Festivalgelände in 60 Sekunden.','🎭 Stelle einen verlorenen Clubbesucher pantomimisch dar.','🎭 Erkläre Kopfhörer ohne Ohr, Musik oder hören.','🎭 Zeichne einen DJ-Controller ohne Buchstaben.','🎭 Stelle jemanden dar, der durch eine volle Tanzfläche geht.','🎭 Erkläre Bass ohne Ton, tief oder Lautsprecher.','🎭 Zeichne eine Discokugel ohne zu sprechen.'];
begin
  select * into r from public.party_rooms where id = p_room;
  select * into m from public.party_members where id = p_member;

  -- Aussetzen: Wurf verfällt, Ereignis anzeigen, event_next gibt den Zug weiter.
  if m.skip then
    update public.party_members set skip = false where id = m.id;
    update public.party_rooms set roll = null, roll_info = jsonb_build_object('skipped', true),
      phase = 'event', task = '🚫 ' || m.name || ' setzt aus (Einlasskontrolle).', timer_started_at = null
    where id = r.id;
    return;
  end if;

  white := floor(random() * 6)::int + 1;
  f := floor(random() * 6)::int + 1;
  total := case f when 1 then white when 2 then white + 2 when 3 then white + 3
                  when 4 then white + 5 when 5 then white + 7 else white * 2 end;
  club_name := case f when 1 then 'Stromausfall' when 5 then 'Bass Drop' when 6 then 'Doppelzeit' else null end;

  raw := m.position + total;
  gained := raw / 64;
  newpos := raw % 64;
  newlap := m.lap + gained;

  -- Sieg: letzte Runde vollendet, Figur bleibt am Einlass stehen.
  if gained > 0 and newlap >= r.laps then
    update public.party_members set position = 0, lap = r.laps where id = m.id;
    update public.party_rooms set roll = total,
      roll_info = jsonb_build_object('white', white, 'club', faces[f], 'club_name', club_name, 'total', total, 'lap', r.laps, 'player', m.id),
      status = 'finished', phase = 'finished',
      task = '🏆 ' || m.name || ' hat ' || r.laps || ' Runden geschafft!', timer_started_at = null
    where id = r.id;
    return;
  end if;

  -- Über den Einlass gezogen: Karte (oder Volltreffer bei genauer Landung)
  if gained > 0 then
    if newpos = 0 then
      update public.party_members set cash = cash + 200 where id = m.id;
      gate := '🎯 Volltreffer am Einlass: +200 Cash';
    elsif random() < 0.6 then
      update public.party_members set cash = cash + 100 where id = m.id;
      gate := '📋 Gästeliste: +100 Cash';
    else
      update public.party_members set skip = true where id = m.id;
      gate := '🚫 Einlasskontrolle: nächste Runde aussetzen';
    end if;
  end if;

  update public.party_members set position = newpos, lap = newlap where id = m.id;
  info := jsonb_build_object('white', white, 'club', faces[f], 'club_name', club_name, 'total', total,
                             'gate', gate, 'lap', newlap, 'player', m.id, 'from', m.position, 'to', newpos);

  if newpos = 0 then
    update public.party_rooms set roll = total, roll_info = info, phase = 'event',
      task = coalesce(gate, '🚪 Einlass'), timer_started_at = null where id = r.id;
  elsif newpos in (5,12,19,26,32,38,45,50,56,60) then
    update public.party_rooms set roll = total, roll_info = info, phase = 'slf',
      timer_started_at = clock_timestamp(), slf_deadline = clock_timestamp() + interval '90 seconds',
      slf_letter = (array['A','B','D','E','F','G','H','K','L','M','N','P','R','S','T','W'])[floor(random()*16)::int + 1],
      task = 'Stadt Land Fluss' where id = r.id;
  elsif newpos = any(acts) then
    update public.party_rooms set roll = total, roll_info = info, phase = 'task',
      task = tasks[(array_position(acts, newpos) - 1) % 12 + 1], timer_started_at = null where id = r.id;
  elsif newpos in (7,17,28,40,49,58) then
    effect := case when newpos in (7,28,49) then 3 else -2 end;
    target := greatest(1, least(63, newpos + effect));
    update public.party_members set position = target where id = m.id;
    event_text := case when effect > 0 then '🎲 Spezial: Turbo! 3 Felder vor.' else '🎲 Spezial: Umweg! 2 Felder zurück.' end;
    update public.party_rooms set roll = total, roll_info = info || jsonb_build_object('to', target), phase = 'event',
      task = event_text, timer_started_at = null where id = r.id;
  elsif newpos in (1,3,8,10,14,15,21,23,24,29,31,34,36,41,43,47,52,54) then
    effect := case when newpos % 2 = 0 then 2 else -2 end;
    target := greatest(1, least(63, newpos + effect));
    update public.party_members set position = target where id = m.id;
    event_text := case when effect > 0 then '⚡ Rückenwind! 2 Felder vor.' else '⚡ Rückschlag! 2 Felder zurück.' end;
    update public.party_rooms set roll = total, roll_info = info || jsonb_build_object('to', target), phase = 'event',
      task = event_text, timer_started_at = null where id = r.id;
  else
    raise exception 'Feld ohne Funktion: %', newpos;
  end if;
end
$function$;

revoke all on function public.party_circuit_roll(uuid, uuid) from public, anon, authenticated;

-- party_action: Start im Rundkurs-Modus + Rundkurs-Wurf. Klassischer Pfad bleibt unverändert.
do $migration$
declare def text; new_def text;
begin
  def := pg_get_functiondef('public.party_action(text,uuid,uuid,text)'::regprocedure);

  new_def := replace(def,
$a$if p_action='start' then$a$,
$b$if p_action in ('start_circuit','start_circuit_3') then
if r.host_token is distinct from p_host_token then raise exception 'Nur Host kann starten'; end if;
if n<2 then raise exception 'Mindestens zwei Spieler'; end if;
if r.status<>'lobby' then raise exception 'Spiel bereits gestartet'; end if;
update public.party_members set position=0,lap=0,cash=0,skip=false where room_id=r.id;
update public.party_rooms set status='playing',phase='ready',turn_index=0,timer_started_at=null,board_mode='circuit',laps=case when p_action='start_circuit_3' then 3 else 2 end,roll_info=null where id=r.id;
elsif p_action='start' then$b$);
  if new_def = def then raise exception 'Migration: Startzweig nicht gefunden'; end if;
  def := new_def;

  new_def := replace(def,
$a$if r.status<>'playing' or r.phase<>'ready' or idx<>(r.turn_index%n) then raise exception 'Nicht dein Zug'; end if;
dice:=$a$,
$b$if r.status<>'playing' or r.phase<>'ready' or idx<>(r.turn_index%n) then raise exception 'Nicht dein Zug'; end if;
if r.board_mode='circuit' then perform public.party_circuit_roll(r.id,m.id); return public.party_snapshot(p_code,p_token); end if;
dice:=$b$);
  if new_def = def then raise exception 'Migration: Wurfzweig nicht gefunden'; end if;

  execute new_def;
end
$migration$;

-- party_snapshot: Runde, Cash, Aussetzen pro Spieler; Modus, Rundenzahl, Wurfdetails pro Raum.
do $migration$
declare def text; new_def text;
begin
  def := pg_get_functiondef('public.party_snapshot(text,uuid)'::regprocedure);
  new_def := replace(def, $a$'position',position,'points',points)$a$,
                          $b$'position',position,'points',points,'lap',lap,'cash',cash,'skip',skip)$b$);
  if new_def = def then raise exception 'Migration: Spielerliste nicht gefunden'; end if;
  def := new_def;
  new_def := replace(def, $a$'your_id',m.id,$a$,
                          $b$'your_id',m.id,'board_mode',r.board_mode,'laps',r.laps,'roll_info',r.roll_info,$b$);
  if new_def = def then raise exception 'Migration: Rückgabeobjekt nicht gefunden'; end if;
  execute new_def;
end
$migration$;
