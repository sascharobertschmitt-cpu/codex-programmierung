-- Entscheidungen auf dem Brett (nur board_mode='circuit'):
--  * Club-Shop vor dem Wurf: Turbo-Würfel (100 Cash, +W6 für diesen Wurf), VIP-Bändchen (150 Cash, schützt einmal
--    vor Schaden: negative Ereigniskarte oder Einlasskontrolle). Maximal 2 Bändchen.
--  * VIP-Treppen auf Feld 20 und 44: Wer dort landet, darf 100 Cash zahlen und 6 Felder abkürzen (Phase 'choice').
--  * Rempler: Wer auf einem Feld mit Mitspielern landet, schnappt sich bis zu 50 Cash vom reichsten von ihnen.
-- Wurf-Logik aufgeteilt: party_circuit_roll (bewegen) -> party_circuit_land (Feldfunktion).

alter table public.party_members
  add column if not exists vip integer not null default 0,
  add column if not exists turbo boolean not null default false;

-- Feldfunktion am aktuellen Standort des Spielers ausführen
create or replace function public.party_circuit_land(p_room uuid, p_member uuid, p_total int, p_info jsonb)
returns void
language plpgsql
security definer
set search_path to ''
as $function$
declare
  r public.party_rooms; m public.party_members; info jsonb := p_info;
  acts int[] := array[2,4,6,9,11,13,16,18,20,22,25,27,30,33,35,37,39,42,44,46,48,51,53,55,57,59,61,62,63];
  tasks text[] := array['🎭 Stelle einen DJ mit kaputtem Mischpult pantomimisch dar.','🎭 Erkläre Afterhour ohne Morgen, Party oder Feiern.','🎭 Zeichne einen Plattenspieler, ohne zu sprechen.','🎭 Stelle einen Türsteher pantomimisch dar.','🎭 Erkläre Nebelmaschine ohne Nebel, Rauch oder Maschine.','🎭 Zeichne ein Festivalgelände in 60 Sekunden.','🎭 Stelle einen verlorenen Clubbesucher pantomimisch dar.','🎭 Erkläre Kopfhörer ohne Ohr, Musik oder hören.','🎭 Zeichne einen DJ-Controller ohne Buchstaben.','🎭 Stelle jemanden dar, der durch eine volle Tanzfläche geht.','🎭 Erkläre Bass ohne Ton, tief oder Lautsprecher.','🎭 Zeichne eine Discokugel ohne zu sprechen.'];
  victim public.party_members; got int; pos int;
begin
  select * into r from public.party_rooms where id = p_room;
  select * into m from public.party_members where id = p_member;
  pos := m.position;

  -- Rempler: Mitspieler auf demselben Feld (nicht am Einlass)
  if pos <> 0 and info->'rempler' is null then
    select * into victim from public.party_members where room_id = r.id and id <> m.id and position = pos and cash > 0
      order by cash desc, joined_at limit 1;
    if found then
      got := least(50, victim.cash);
      update public.party_members set cash = cash - got where id = victim.id;
      update public.party_members set cash = cash + got where id = m.id;
      info := info || jsonb_build_object('rempler', jsonb_build_object('victim', victim.name, 'got', got));
    end if;
  end if;

  if pos = 0 then
    update public.party_rooms set roll = p_total, roll_info = info, phase = 'event',
      task = coalesce(info->>'gate', '🚪 Einlass'), timer_started_at = null where id = r.id;
  elsif pos in (5,12,19,26,32,38,45,50,56,60) then
    update public.party_rooms set roll = p_total, roll_info = info, phase = 'slf',
      timer_started_at = clock_timestamp(), slf_deadline = clock_timestamp() + interval '90 seconds',
      slf_letter = (array['A','B','D','E','F','G','H','K','L','M','N','P','R','S','T','W'])[floor(random()*16)::int + 1],
      task = 'Stadt Land Fluss' where id = r.id;
  elsif pos = any(acts) then
    update public.party_rooms set roll = p_total, roll_info = info, phase = 'task',
      task = tasks[(array_position(acts, pos) - 1) % 12 + 1], timer_started_at = null where id = r.id;
  elsif pos in (7,17,28,40,49,58) then
    perform public.party_circuit_card(r.id, m.id, 'aufgabe', p_total, info);
  elsif pos in (1,3,8,10,14,15,21,23,24,29,31,34,36,41,43,47,52,54) then
    perform public.party_circuit_card(r.id, m.id, 'ereignis', p_total, info);
  else
    raise exception 'Feld ohne Funktion: %', pos;
  end if;
end
$function$;
revoke all on function public.party_circuit_land(uuid, uuid, int, jsonb) from public, anon, authenticated;

create or replace function public.party_circuit_roll(p_room uuid, p_member uuid)
returns void
language plpgsql
security definer
set search_path to ''
as $function$
declare
  r public.party_rooms; m public.party_members;
  faces text[] := array['0','2','3','5','7','×2'];
  white int; f int; total int; raw int; gained int; newpos int; newlap int; extra int := null;
  club_name text; gate text := null; info jsonb;
begin
  select * into r from public.party_rooms where id = p_room;
  select * into m from public.party_members where id = p_member;

  if m.skip then
    update public.party_members set skip = false where id = m.id;
    update public.party_rooms set roll = null, roll_info = jsonb_build_object('skipped', true, 'player', m.id),
      phase = 'event', task = '🚫 ' || m.name || ' setzt aus.', timer_started_at = null
    where id = r.id;
    return;
  end if;

  white := floor(random() * 6)::int + 1;
  f := floor(random() * 6)::int + 1;
  total := case f when 1 then white when 2 then white + 2 when 3 then white + 3
                  when 4 then white + 5 when 5 then white + 7 else white * 2 end;
  club_name := case f when 1 then 'Stromausfall' when 5 then 'Bass Drop' when 6 then 'Doppelzeit' else null end;
  if m.turbo then
    extra := floor(random() * 6)::int + 1;
    total := total + extra;
    update public.party_members set turbo = false where id = m.id;
  end if;

  raw := m.position + total;
  gained := raw / 64;
  newpos := raw % 64;
  newlap := m.lap + gained;

  if gained > 0 and newlap >= r.laps then
    update public.party_members set position = 0, lap = r.laps where id = m.id;
    update public.party_rooms set roll = total,
      roll_info = jsonb_build_object('white', white, 'club', faces[f], 'club_name', club_name, 'total', total, 'turbo', extra,
                                     'lap', r.laps, 'player', m.id, 'from', m.position, 'to', 0),
      status = 'finished', phase = 'finished',
      task = '🏆 ' || m.name || ' hat ' || r.laps || ' Runden geschafft!', timer_started_at = null
    where id = r.id;
    return;
  end if;

  if gained > 0 then
    if newpos = 0 then
      update public.party_members set cash = cash + 200 where id = m.id;
      gate := '🎯 Volltreffer am Einlass: +200 Cash';
    elsif random() < 0.6 then
      update public.party_members set cash = cash + 100 where id = m.id;
      gate := '📋 Gästeliste: +100 Cash';
    elsif m.vip > 0 then
      update public.party_members set vip = vip - 1 where id = m.id;
      gate := '🛡️ Einlasskontrolle, aber das VIP-Bändchen zieht: kein Aussetzen';
    else
      update public.party_members set skip = true where id = m.id;
      gate := '🚫 Einlasskontrolle: nächste Runde aussetzen';
    end if;
  end if;

  update public.party_members set position = newpos, lap = newlap where id = m.id;
  info := jsonb_build_object('white', white, 'club', faces[f], 'club_name', club_name, 'total', total, 'turbo', extra,
                             'gate', gate, 'lap', newlap, 'player', m.id, 'from', m.position, 'to', newpos);

  -- VIP-Treppe: Entscheidung abwarten, wenn genug Cash da ist
  if newpos in (20, 44) and (select cash from public.party_members where id = m.id) >= 100 then
    update public.party_rooms set roll = total, roll_info = info || jsonb_build_object('stairs', newpos),
      phase = 'choice', task = '⭐ VIP-Treppe: 100 Cash zahlen und 6 Felder abkürzen?', timer_started_at = null
    where id = r.id;
    return;
  end if;

  perform public.party_circuit_land(r.id, m.id, total, info);
end
$function$;
revoke all on function public.party_circuit_roll(uuid, uuid) from public, anon, authenticated;

-- VIP-Bändchen schützt vor negativen Ereigniskarten
do $migration$
declare def text; new_def text;
begin
  def := pg_get_functiondef('public.party_circuit_card(uuid,uuid,text,integer,jsonb)'::regprocedure);
  new_def := replace(def,
$a$  target := m.position;
  if c.kind = 'move' then$a$,
$b$  target := m.position;
  if m.vip > 0 and ((c.kind in ('move', 'cash') and c.value < 0) or c.kind in ('skip', 'treat')) then
    update public.party_members set vip = vip - 1 where id = m.id;
    card := card || jsonb_build_object('blocked', true);
    update public.party_rooms set roll = p_total, roll_info = p_info || jsonb_build_object('to', target, 'card', card),
      phase = 'event', task = '🃏 ' || c.title || ': ' || c.body || ' · 🛡️ VIP-Bändchen schützt dich!', timer_started_at = null
    where id = r.id;
    return;
  end if;
  if c.kind = 'move' then$b$);
  if new_def = def then raise exception 'Migration: Kartenwirkung nicht gefunden'; end if;
  execute new_def;

  -- party_action: Shop und Treppen-Entscheidung
  def := pg_get_functiondef('public.party_action(text,uuid,uuid,text)'::regprocedure);
  new_def := replace(def,
$a$elsif p_action='event_next' then$a$,
$b$elsif p_action in ('buy_turbo','buy_vip') then
if r.board_mode<>'circuit' or r.status<>'playing' or r.phase<>'ready' or idx<>(r.turn_index%n) then raise exception 'Shop nur vor deinem Wurf'; end if;
if p_action='buy_turbo' then
if m.turbo then raise exception 'Turbo-Würfel ist schon aktiv'; end if;
if m.cash<100 then raise exception 'Zu wenig Cash (100 nötig)'; end if;
update public.party_members set cash=cash-100,turbo=true where id=m.id;
else
if m.vip>=2 then raise exception 'Maximal 2 VIP-Bändchen'; end if;
if m.cash<150 then raise exception 'Zu wenig Cash (150 nötig)'; end if;
update public.party_members set cash=cash-150,vip=vip+1 where id=m.id;
end if;
elsif p_action in ('stairs_yes','stairs_no') then
if r.phase<>'choice' or r.status<>'playing' then raise exception 'Keine Entscheidung offen'; end if;
if idx<>(r.turn_index%n) then raise exception 'Nur der aktive Spieler entscheidet'; end if;
if p_action='stairs_yes' and m.cash>=100 then
update public.party_members set cash=cash-100,position=least(63,position+6) where id=m.id;
perform public.party_circuit_land(r.id,m.id,r.roll,r.roll_info||jsonb_build_object('stairs_used',true,'to',least(63,m.position+6)));
else
perform public.party_circuit_land(r.id,m.id,r.roll,r.roll_info||jsonb_build_object('stairs_used',false));
end if;
elsif p_action='event_next' then$b$);
  if new_def = def then raise exception 'Migration: event_next nicht gefunden'; end if;
  execute new_def;

  -- Snapshot: vip und turbo pro Spieler
  def := pg_get_functiondef('public.party_snapshot(text,uuid)'::regprocedure);
  new_def := replace(def, $a$'is_bot',is_bot,'hat',hat)$a$, $b$'is_bot',is_bot,'hat',hat,'vip',vip,'turbo',turbo)$b$);
  if new_def = def then raise exception 'Migration: Snapshot-Spielerliste nicht gefunden'; end if;
  execute new_def;

  -- Bots: Treppe nehmen, manchmal Turbo kaufen
  def := pg_get_functiondef('public.party_bot_tick(text,uuid)'::regprocedure);
  new_def := replace(def,
$a$  if r.phase = 'ready' and act.is_bot then
    perform public.party_action(p_code, act.token, null, 'roll');
    did := 'roll';$a$,
$b$  if r.phase = 'ready' and act.is_bot then
    if r.board_mode = 'circuit' and not act.turbo and act.cash >= 250 and random() < 0.5 then
      perform public.party_action(p_code, act.token, null, 'buy_turbo');
    elsif r.board_mode = 'circuit' and act.vip = 0 and act.cash >= 300 and random() < 0.4 then
      perform public.party_action(p_code, act.token, null, 'buy_vip');
    end if;
    perform public.party_action(p_code, act.token, null, 'roll');
    did := 'roll';
  elsif r.phase = 'choice' and act.is_bot then
    perform public.party_action(p_code, act.token, null, case when act.cash >= 100 and random() < 0.65 then 'stairs_yes' else 'stairs_no' end);
    did := 'choice';$b$);
  if new_def = def then raise exception 'Migration: Bot-Wurfzweig nicht gefunden'; end if;
  execute new_def;
end
$migration$;
