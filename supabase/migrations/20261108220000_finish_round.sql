-- Wer zuerst ankommt, beendet das Spiel nicht sofort: die laufende Runde wird zu Ende gespielt.
alter table public.party_rooms add column if not exists ending_at int;

create or replace function public.party_round_end() returns trigger
language plpgsql security definer set search_path to '' as $f$
declare w public.party_members;
begin
  if new.ending_at is not null and new.status = 'playing' and new.turn_index is distinct from old.turn_index
     and new.turn_index >= new.ending_at then
    select * into w from public.party_members where room_id = new.id order by stars desc, cash desc, joined_at limit 1;
    new.status := 'finished'; new.phase := 'finished'; new.timer_started_at := null;
    new.task := '🏆 ' || w.name || ' gewinnt mit ' || w.stars || ' ⭐!';
    new.roll_info := coalesce(new.roll_info, '{}'::jsonb) || jsonb_build_object('winner', w.name);
  end if;
  return new;
end $f$;
drop trigger if exists party_round_end on public.party_rooms;
create trigger party_round_end before update of turn_index on public.party_rooms
  for each row execute function public.party_round_end();

do $do$
declare d text; n text;
begin
  d := pg_get_functiondef('public.party_circuit_roll'::regproc);
  n := replace(d, $a$    update public.party_members set position = 0, lap = r.laps, stars = stars + 1 where id = m.id;
    select * into w from public.party_members where room_id = r.id order by stars desc, cash desc, joined_at limit 1;
    update public.party_rooms set roll = total,
      roll_info = jsonb_build_object('white', white, 'club', faces[f], 'club_name', club_name, 'total', total, 'turbo', extra,
                                     'lap', r.laps, 'player', m.id, 'from', m.position, 'to', 0, 'finisher', m.name, 'winner', w.name),
      status = 'finished', phase = 'finished',
      task = '🏆 ' || w.name || ' gewinnt mit ' || w.stars || ' ⭐! ' || m.name || ' war als Erste/r im Ziel (+1 Zielstern).', timer_started_at = null
    where id = r.id;$a$,
  $b$    update public.party_members set position = 0, lap = r.laps,
      stars = stars + case when r.ending_at is null then 1 else 0 end where id = m.id;
    update public.party_rooms set roll = total,
      roll_info = jsonb_build_object('white', white, 'club', faces[f], 'club_name', club_name, 'total', total, 'turbo', extra,
                                     'lap', r.laps, 'player', m.id, 'from', m.position, 'to', 0, 'finish', true, 'first', r.ending_at is null),
      phase = 'event',
      ending_at = coalesce(r.ending_at, (r.turn_index / (select count(*) from public.party_members where room_id = r.id) + 1)
                                         * (select count(*) from public.party_members where room_id = r.id)),
      task = case when r.ending_at is null then '🏁 ' || m.name || ' ist als Erste/r im Ziel: +1 Zielstern! Die Runde wird noch zu Ende gespielt.'
                  else '🏁 ' || m.name || ' ist auch im Ziel.' end,
      timer_started_at = null
    where id = r.id;$b$);
  if n = d then raise exception 'party_circuit_roll unerwartet'; end if;
  execute n;
  d := pg_get_functiondef('public.party_action'::regproc);
  n := replace(d, $a$roll_info=null,star_field=null,$a$, $b$roll_info=null,ending_at=null,star_field=null,$b$);
  if n = d then raise exception 'party_action unerwartet'; end if;
  execute n;
  d := pg_get_functiondef('public.party_snapshot'::regproc);
  n := replace(d, $a$'star_price',150,$a$, $b$'star_price',150,'final_round',r.ending_at is not null,$b$);
  if n = d then raise exception 'party_snapshot unerwartet'; end if;
  execute n;
end
$do$;
