-- Sterne wie bei Mario Party: am Sternhändler für 150 Münzen kaufen, Sterne entscheiden das Spiel.
alter table public.party_members add column if not exists stars int not null default 0;
alter table public.party_rooms add column if not exists star_field int;

-- Münzen für Aufgaben und SLF im Rundkurs: Activity geschafft +30, SLF-Punkte 1:1 als Münzen
create or replace function public.party_points_to_coins() returns trigger
language plpgsql security definer set search_path to '' as $f$
declare d int := new.points - old.points;
begin
  if d > 0 and exists (select 1 from public.party_rooms where id = new.room_id and board_mode = 'circuit') then
    new.cash := new.cash + case when d = 1 then 30 else d end;
  end if;
  return new;
end $f$;
drop trigger if exists party_points_to_coins on public.party_members;
create trigger party_points_to_coins before update of points on public.party_members
  for each row execute function public.party_points_to_coins();

-- Neues Sternfeld: Activity- oder Ereignisfeld, mindestens 12 Felder vom alten entfernt
create or replace function public.party_new_star_field(p_old int) returns int
language sql volatile set search_path to '' as $f$
  select f from unnest(array[3,5,7,9,11,13,15,17,19,23,25,27,29,31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,63,65,67,69,71,73,75,77]) f
  where p_old is null or least(abs(f - p_old), 80 - abs(f - p_old)) >= 12
  order by random() limit 1
$f$;

-- Nach Sternhändler: kaufen oder nicht, dann VIP-Treppe prüfen oder Feld auslösen
create or replace function public.party_circuit_star(p_room uuid, p_member uuid, p_buy boolean)
returns void language plpgsql security definer set search_path to '' as $f$
declare r public.party_rooms; m public.party_members; info jsonb;
begin
  select * into r from public.party_rooms where id = p_room;
  select * into m from public.party_members where id = p_member;
  info := r.roll_info - 'star_offer';
  if p_buy and m.cash >= 150 then
    update public.party_members set cash = cash - 150, stars = stars + 1 where id = m.id;
    update public.party_rooms set star_field = public.party_new_star_field(r.star_field) where id = r.id;
    info := info || jsonb_build_object('star_bought', true);
    m.cash := m.cash - 150;
  else
    info := info || jsonb_build_object('star_bought', false);
  end if;
  if m.position in (21, 61) and m.cash >= 100 then
    update public.party_rooms set roll_info = info || jsonb_build_object('stairs', m.position), phase = 'choice',
      task = '⭐ VIP-Treppe: 100 Münzen zahlen und 6 Felder abkürzen?', timer_started_at = null where id = r.id;
    return;
  end if;
  perform public.party_circuit_land(r.id, m.id, r.roll, info);
end $f$;

create or replace function public.party_circuit_roll(p_room uuid, p_member uuid)
 returns void language plpgsql security definer set search_path to ''
as $function$
declare
  r public.party_rooms; m public.party_members; w public.party_members;
  faces text[] := array['0','2','3','5','7','×2'];
  white int; f int; total int; raw int; gained int; newpos int; newlap int; extra int := null;
  club_name text; gate text := null; info jsonb; dist int;
begin
  select * into r from public.party_rooms where id = p_room;
  select * into m from public.party_members where id = p_member;
  if r.star_field is null then
    r.star_field := public.party_new_star_field(null);
    update public.party_rooms set star_field = r.star_field where id = r.id;
  end if;
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
  gained := raw / 80;
  newpos := raw % 80;
  newlap := m.lap + gained;
  if gained > 0 and newlap >= r.laps then
    -- Ziel: Zielstern für den Ersten, Sieger ist wer die meisten Sterne hat
    update public.party_members set position = 0, lap = r.laps, stars = stars + 1 where id = m.id;
    select * into w from public.party_members where room_id = r.id order by stars desc, cash desc, joined_at limit 1;
    update public.party_rooms set roll = total,
      roll_info = jsonb_build_object('white', white, 'club', faces[f], 'club_name', club_name, 'total', total, 'turbo', extra,
                                     'lap', r.laps, 'player', m.id, 'from', m.position, 'to', 0, 'finisher', m.name, 'winner', w.name),
      status = 'finished', phase = 'finished',
      task = '🏆 ' || w.name || ' gewinnt mit ' || w.stars || ' ⭐! ' || m.name || ' war als Erste/r im Ziel (+1 Zielstern).', timer_started_at = null
    where id = r.id;
    return;
  end if;
  if gained > 0 then
    if newpos = 0 then
      update public.party_members set cash = cash + 200 where id = m.id;
      gate := '🎯 Volltreffer am Einlass: +200 Münzen';
    elsif random() < 0.6 then
      update public.party_members set cash = cash + 100 where id = m.id;
      gate := '📋 Gästeliste: +100 Münzen';
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
  -- Sternhändler unterwegs passiert oder erreicht
  dist := ((r.star_field - m.position) % 80 + 80) % 80;
  if dist between 1 and total and (select cash from public.party_members where id = m.id) >= 150 then
    update public.party_rooms set roll = total, roll_info = info || jsonb_build_object('star_offer', true), phase = 'choice',
      task = '⭐ Du kommst am Sternhändler vorbei: 1 Stern für 150 Münzen kaufen?', timer_started_at = null
    where id = r.id;
    return;
  end if;
  if newpos in (21, 61) and (select cash from public.party_members where id = m.id) >= 100 then
    update public.party_rooms set roll = total, roll_info = info || jsonb_build_object('stairs', newpos),
      phase = 'choice', task = '⭐ VIP-Treppe: 100 Münzen zahlen und 6 Felder abkürzen?', timer_started_at = null
    where id = r.id;
    return;
  end if;
  perform public.party_circuit_land(r.id, m.id, total, info);
end
$function$;

do $do$
declare d text; n text;
begin
  -- Aktionen star_yes / star_no, Neustart setzt Sterne zurück
  d := pg_get_functiondef('public.party_action'::regproc);
  n := replace(d, $a$elsif p_action in ('stairs_yes','stairs_no') then$a$,
    $b$elsif p_action in ('star_yes','star_no') then
if r.phase<>'choice' or not (coalesce(r.roll_info,'{}'::jsonb) ? 'star_offer') then raise exception 'Kein Sternkauf offen'; end if;
if idx<>(r.turn_index%n) then raise exception 'Nur der aktive Spieler entscheidet'; end if;
perform public.party_circuit_star(r.id,m.id,p_action='star_yes');
elsif p_action in ('stairs_yes','stairs_no') then$b$);
  n := replace(n, 'update public.party_members set position=0,lap=0,cash=0,skip=false where room_id=r.id;',
                  'update public.party_members set position=0,lap=0,cash=0,skip=false,stars=0,points=0,vip=0,turbo=false where room_id=r.id;');
  n := replace(n, $a$laps=case when p_action='start_circuit_3' then 3 else 2 end,roll_info=null where id=r.id;$a$,
                  $b$laps=case when p_action='start_circuit_3' then 3 else 2 end,roll_info=null,star_field=null,used_tasks='{}',used_cards='{}' where id=r.id;$b$);
  if n not like '%star_yes%' or n not like '%stars=0%' or n not like '%star_field=null%' then raise exception 'party_action unerwartet'; end if;
  execute n;
  -- Bots: Sternhändler
  d := pg_get_functiondef('public.party_bot_tick'::regproc);
  n := replace(d, $a$case when act.cash >= 100 and random() < 0.65 then 'stairs_yes' else 'stairs_no' end$a$,
    $b$case when r.roll_info ? 'star_offer' then (case when act.cash >= 150 then 'star_yes' else 'star_no' end) when act.cash >= 100 and random() < 0.65 then 'stairs_yes' else 'stairs_no' end$b$);
  n := replace(replace(n, '+1 Punkt, +', '+30 Münzen, +'), '+1 Punkt''', '+30 Münzen''');
  n := replace(n, ' Cash'' where id = r.id', ' Münzen'' where id = r.id');
  if n not like '%star_offer%' then raise exception 'party_bot_tick unerwartet'; end if;
  execute n;
  -- Snapshot: Sterne und Sternfeld
  d := pg_get_functiondef('public.party_snapshot'::regproc);
  n := replace(d, $a$'vip',vip,'turbo',turbo)$a$, $b$'vip',vip,'turbo',turbo,'stars',stars)$b$);
  n := replace(n, $a$'laps',r.laps,$a$, $b$'laps',r.laps,'star_field',r.star_field,'star_price',150,$b$);
  if n not like '%star_field%' or n not like '%''stars'',stars%' then raise exception 'party_snapshot unerwartet'; end if;
  execute n;
end
$do$;
