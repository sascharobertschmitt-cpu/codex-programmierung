-- Kartenstapel in der Mitte des Rundkurses.
-- Ereignisfelder ziehen eine Ereigniskarte (sofortige Wirkung), Spezialfelder eine Aufgabenkarte
-- (Sonderaufgabe mit Timer und Bewertung, Belohnung in Cash). Nur board_mode='circuit'; klassisch unverändert.

create table if not exists public.party_cards (
  id serial primary key,
  deck text not null check (deck in ('ereignis','aufgabe')),
  title text not null,
  body text not null,
  kind text not null default 'task',
  value integer not null default 0,
  unique (deck, title)
);
alter table public.party_cards enable row level security;
revoke all on public.party_cards from anon, authenticated;

insert into public.party_cards (deck, title, body, kind, value) values
    ('ereignis','Gästeliste vom Promoter','Dein Name steht doch drauf. +100 Cash','cash',100),
    ('ereignis','Garderobenmarke weg','Die Jacke ist erst mal verschollen. −50 Cash','cash',-50),
    ('ereignis','Bass Drop','Der Drop zieht dich nach vorne. 3 Felder vor','move',3),
    ('ereignis','Klo-Schlange','Zwanzig Minuten anstehen. 2 Felder zurück','move',-2),
    ('ereignis','Nebelmaschine','Du siehst nichts mehr und läufst falsch. 2 Felder zurück','move',-2),
    ('ereignis','Dein Track läuft','Der DJ spielt genau deine Nummer. 2 Felder vor','move',2),
    ('ereignis','Hinterausgang','Jemand vom Team lässt dich durch. 4 Felder vor','move',4),
    ('ereignis','Handy weg','Du suchst es auf dem ganzen Floor. Einmal aussetzen','skip',0),
    ('ereignis','Frische Luft','Kurz raus in den Raucherbereich. 1 Feld zurück','move',-1),
    ('ereignis','Runde für alle','Du gibst aus: alle anderen +50 Cash, du −50','treat',50),
    ('ereignis','Stromausfall','Alle anderen stolpern im Dunkeln 1 Feld zurück','others_back',1),
    ('ereignis','Merch-Stand','Shirt gekauft. −100 Cash','cash',-100),
    ('ereignis','Pfand gesammelt','Der Floor war voller Flaschen. +50 Cash','cash',50),
    ('ereignis','Türsteher nickt','Du kommst ohne Diskussion durch. 3 Felder vor','move',3),
    ('ereignis','Strobo-Gewitter','Kurz orientierungslos. 1 Feld zurück','move',-1),
    ('ereignis','Back-to-Back','Du legst spontan mit auf. +150 Cash Gage','cash',150),
    ('ereignis','Glitzerregen','Alle feiern mit: jeder bekommt +50 Cash','cash_all',50),
    ('ereignis','Taschendieb','Du holst dir 100 Cash vom reichsten Mitspieler','rob_leader',100),
    ('ereignis','Zu viel Mate','Du drehst eine Extrarunde über den Floor. 2 Felder vor','move',2),
    ('ereignis','Sperrstunde droht','Alle anderen 2 Felder zurück','others_back',2),
    ('aufgabe','Air-DJ','Mix 30 Sekunden pantomimisch zwei Tracks ineinander, mit Filter und Drop. Die Runde muss den Drop erkennen.','task',150),
    ('aufgabe','Beatbox','Mach 20 Sekunden lang einen Techno-Beat nur mit dem Mund.','task',150),
    ('aufgabe','Summ-Raten','Summe einen bekannten Song. Jemand muss ihn innerhalb von 30 Sekunden erraten.','task',200),
    ('aufgabe','Türsteher-Check','Überzeuge die Runde in 30 Sekunden, warum du heute rein darfst.','task',150),
    ('aufgabe','Neuer Move','Erfinde einen Tanz-Move mit Namen und bring ihn allen bei.','task',100),
    ('aufgabe','130 BPM','Klatsche zehn Sekunden lang 130 BPM. Jemand prüft mit einem Metronom.','task',150),
    ('aufgabe','Rave-Wörter','Nenne in 30 Sekunden zehn Begriffe rund um Techno, ohne Wiederholung.','task',100),
    ('aufgabe','Flyer-Spruch','Denk dir einen Partynamen mit Slogan aus. Die Runde muss lachen oder nicken.','task',100),
    ('aufgabe','Garderobe zeigen','Erkläre jemandem nur mit Handzeichen, wo die Garderobe ist.','task',100),
    ('aufgabe','MC-Ansage','Kündige den Headliner an, als stündest du vor 3000 Leuten.','task',150),
    ('aufgabe','Dominik-Moment','Erzähl in 45 Sekunden die absurdeste Club-Story, die du dir ausdenken kannst.','task',200),
    ('aufgabe','Line-up','Nenne in 30 Sekunden fünf DJs oder Live-Acts aus der Techno-Szene.','task',150)
on conflict (deck, title) do update set body = excluded.body, kind = excluded.kind, value = excluded.value;

create or replace function public.party_circuit_card(p_room uuid, p_member uuid, p_deck text, p_total int, p_info jsonb)
returns void
language plpgsql
security definer
set search_path to ''
as $function$
declare
  r public.party_rooms; m public.party_members; c public.party_cards;
  target int; victim public.party_members; got int; card jsonb;
begin
  select * into r from public.party_rooms where id = p_room;
  select * into m from public.party_members where id = p_member;
  -- zufällige Karte, die zuletzt gezogene nicht direkt wieder
  select * into c from public.party_cards where deck = p_deck
    and title is distinct from (r.roll_info -> 'card' ->> 'title') order by random() limit 1;
  card := jsonb_build_object('deck', c.deck, 'title', c.title, 'body', c.body, 'kind', c.kind, 'value', c.value);

  if p_deck = 'aufgabe' then
    update public.party_rooms set roll = p_total, roll_info = p_info || jsonb_build_object('card', card),
      phase = 'task', task = '⭐ ' || c.title || ': ' || c.body || ' (+' || c.value || ' Cash)', timer_started_at = null
    where id = r.id;
    return;
  end if;

  target := m.position;
  if c.kind = 'move' then
    target := greatest(1, least(63, m.position + c.value));
    update public.party_members set position = target where id = m.id;
  elsif c.kind = 'cash' then
    update public.party_members set cash = greatest(0, cash + c.value) where id = m.id;
  elsif c.kind = 'skip' then
    update public.party_members set skip = true where id = m.id;
  elsif c.kind = 'treat' then
    update public.party_members set cash = cash + c.value where room_id = r.id and id <> m.id;
    update public.party_members set cash = greatest(0, cash - c.value) where id = m.id;
  elsif c.kind = 'cash_all' then
    update public.party_members set cash = cash + c.value where room_id = r.id;
  elsif c.kind = 'others_back' then
    update public.party_members set position = greatest(0, position - c.value) where room_id = r.id and id <> m.id;
  elsif c.kind = 'rob_leader' then
    select * into victim from public.party_members where room_id = r.id and id <> m.id
      order by cash desc, joined_at limit 1;
    if found then
      got := least(c.value, victim.cash);
      update public.party_members set cash = cash - got where id = victim.id;
      update public.party_members set cash = cash + got where id = m.id;
      card := card || jsonb_build_object('victim', victim.name, 'got', got);
    end if;
  end if;

  update public.party_rooms set roll = p_total,
    roll_info = p_info || jsonb_build_object('to', target, 'card', card),
    phase = 'event', task = '🃏 ' || c.title || ': ' || c.body, timer_started_at = null
  where id = r.id;
end
$function$;
revoke all on function public.party_circuit_card(uuid, uuid, text, int, jsonb) from public, anon, authenticated;

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
    perform public.party_circuit_card(r.id, m.id, 'aufgabe', total, info);
  elsif newpos in (1,3,8,10,14,15,21,23,24,29,31,34,36,41,43,47,52,54) then
    perform public.party_circuit_card(r.id, m.id, 'ereignis', total, info);
  else
    raise exception 'Feld ohne Funktion: %', newpos;
  end if;
end
$function$;

revoke all on function public.party_circuit_roll(uuid, uuid) from public, anon, authenticated;

-- Belohnung für gelöste Aufgabenkarten (Mensch bewertet)
do $migration$
declare def text; new_def text;
begin
  def := pg_get_functiondef('public.party_action(text,uuid,uuid,text)'::regprocedure);
  new_def := replace(def,
$a$if p_action='success' then
update public.party_members set points=points+1 where id=(select id from public.party_members where room_id=r.id order by joined_at,id offset (r.turn_index%n) limit 1);
end if;$a$,
$b$if p_action='success' then
update public.party_members set points=points+1 where id=(select id from public.party_members where room_id=r.id order by joined_at,id offset (r.turn_index%n) limit 1);
if r.board_mode='circuit' and r.roll_info->'card'->>'deck'='aufgabe' then
update public.party_members set cash=cash+coalesce((r.roll_info->'card'->>'value')::int,0) where id=(select id from public.party_members where room_id=r.id order by joined_at,id offset (r.turn_index%n) limit 1);
end if;
end if;$b$);
  if new_def = def then raise exception 'Migration: Bewertungszweig nicht gefunden'; end if;
  execute new_def;

  -- Bots: gelöste Aufgabenkarte bringt ebenfalls Cash
  def := pg_get_functiondef('public.party_bot_tick(text,uuid)'::regprocedure);
  new_def := replace(def,
$a$      update public.party_members set points = points + 1 where id = act.id;
      update public.party_rooms set phase = 'event', timer_started_at = null,
        task = act.name || ' hat die Aufgabe gemeistert! +1 Punkt' where id = r.id;$a$,
$b$      update public.party_members set points = points + 1 where id = act.id;
      if r.board_mode = 'circuit' and r.roll_info->'card'->>'deck' = 'aufgabe' then
        update public.party_members set cash = cash + coalesce((r.roll_info->'card'->>'value')::int, 0) where id = act.id;
        update public.party_rooms set phase = 'event', timer_started_at = null,
          task = act.name || ' hat die Aufgabe gemeistert! +1 Punkt, +' || (r.roll_info->'card'->>'value') || ' Cash' where id = r.id;
      else
        update public.party_rooms set phase = 'event', timer_started_at = null,
          task = act.name || ' hat die Aufgabe gemeistert! +1 Punkt' where id = r.id;
      end if;$b$);
  if new_def = def then raise exception 'Migration: Bot-Aufgabenzweig nicht gefunden'; end if;
  execute new_def;
end
$migration$;
