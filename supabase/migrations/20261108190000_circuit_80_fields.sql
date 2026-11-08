-- 80 Felder im Rundkurs, neue Verteilung, Activity-Pool ohne Wiederholung
create table if not exists public.party_tasks (id serial primary key, kind text not null, text text not null unique);
alter table public.party_tasks enable row level security;
alter table public.party_rooms add column if not exists used_tasks int[] not null default '{}';
alter table public.party_rooms add column if not exists used_cards int[] not null default '{}';
insert into public.party_tasks (kind, text) values
('pantomime','🎭 Pantomime: DJ, dessen Laptop mitten im Set abstürzt. Die anderen raten.'),
('pantomime','🎭 Pantomime: Türsteher, der dich nicht reinlässt. Die anderen raten.'),
('pantomime','🎭 Pantomime: Raver, der seine Freunde auf dem Floor sucht. Die anderen raten.'),
('pantomime','🎭 Pantomime: Jemand, der an der Garderobe die Marke verloren hat. Die anderen raten.'),
('pantomime','🎭 Pantomime: Barkeeper beim größten Ansturm der Nacht. Die anderen raten.'),
('pantomime','🎭 Pantomime: Lichttechniker beim Drop. Die anderen raten.'),
('pantomime','🎭 Pantomime: Jemand, der zum ersten Mal Nebel sieht. Die anderen raten.'),
('pantomime','🎭 Pantomime: Tänzer, der den Beat nicht findet. Die anderen raten.'),
('pantomime','🎭 Pantomime: DJ, der den nächsten Track im Kopfhörer vorhört. Die anderen raten.'),
('pantomime','🎭 Pantomime: Schlange vor dem Club im Regen. Die anderen raten.'),
('pantomime','🎭 Pantomime: Jemand, der im Dunkeln sein Handy sucht. Die anderen raten.'),
('pantomime','🎭 Pantomime: Raver, der um 6 Uhr ins Tageslicht tritt. Die anderen raten.'),
('pantomime','🎭 Pantomime: Security beim Abtasten. Die anderen raten.'),
('pantomime','🎭 Pantomime: Fotograf, der heimlich Fotos macht und erwischt wird. Die anderen raten.'),
('pantomime','🎭 Pantomime: Plattensammler, der die perfekte Platte findet. Die anderen raten.'),
('pantomime','🎭 Pantomime: Producer, dem das Projekt abstürzt. Die anderen raten.'),
('pantomime','🎭 Pantomime: Jemand, der im Club telefonieren will. Die anderen raten.'),
('pantomime','🎭 Pantomime: Abendkasse ohne Wechselgeld. Die anderen raten.'),
('pantomime','🎭 Pantomime: DJ mit kaputtem Mischpult. Die anderen raten.'),
('pantomime','🎭 Pantomime: Jemand, der sich durch eine volle Tanzfläche drängelt. Die anderen raten.'),
('pantomime','🎭 Pantomime: Verlorener Clubbesucher. Die anderen raten.'),
('erklaeren','🗣️ Erkläre „Afterhour“ ohne die Wörter Morgen, Party, Feiern.'),
('erklaeren','🗣️ Erkläre „Nebelmaschine“ ohne die Wörter Nebel, Rauch, Maschine.'),
('erklaeren','🗣️ Erkläre „Kopfhörer“ ohne die Wörter Ohr, Musik, hören.'),
('erklaeren','🗣️ Erkläre „Bass“ ohne die Wörter Ton, tief, Lautsprecher.'),
('erklaeren','🗣️ Erkläre „Gästeliste“ ohne die Wörter Name, Liste, Eintritt.'),
('erklaeren','🗣️ Erkläre „Garderobe“ ohne die Wörter Jacke, abgeben, Marke.'),
('erklaeren','🗣️ Erkläre „Stroboskop“ ohne die Wörter Licht, blitzen, schnell.'),
('erklaeren','🗣️ Erkläre „Vinyl“ ohne die Wörter Platte, schwarz, rund.'),
('erklaeren','🗣️ Erkläre „Line-up“ ohne die Wörter DJ, Reihenfolge, Abend.'),
('erklaeren','🗣️ Erkläre „Drop“ ohne die Wörter fallen, Bass, Höhepunkt.'),
('erklaeren','🗣️ Erkläre „Closing-Set“ ohne die Wörter letzte, Ende, DJ.'),
('erklaeren','🗣️ Erkläre „Warm-up“ ohne die Wörter Anfang, früh, aufwärmen.'),
('erklaeren','🗣️ Erkläre „Mischpult“ ohne die Wörter Regler, mischen, DJ.'),
('erklaeren','🗣️ Erkläre „Festival“ ohne die Wörter Zelt, draußen, Bühne.'),
('erklaeren','🗣️ Erkläre „Stempel“ ohne die Wörter Hand, Eintritt, Tinte.'),
('erklaeren','🗣️ Erkläre „Türsteher“ ohne die Wörter Tür, Einlass, groß.'),
('erklaeren','🗣️ Erkläre „Ohrstöpsel“ ohne die Wörter Ohr, laut, Schutz.'),
('erklaeren','🗣️ Erkläre „Tanzfläche“ ohne die Wörter tanzen, Boden, Leute.'),
('erklaeren','🗣️ Erkläre „BPM“ ohne die Wörter Tempo, Schläge, Minute.'),
('erklaeren','🗣️ Erkläre „Spätkauf“ ohne die Wörter Kiosk, nachts, kaufen.'),
('erklaeren','🗣️ Erkläre „Sonnenbrille“ ohne die Wörter Sonne, Augen, Brille.'),
('zeichnen','✏️ Zeichne: Plattenspieler. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Discokugel. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: DJ-Controller ohne Buchstaben. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Festivalgelände. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Türsteher. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Lautsprecherturm. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Lichtshow mit Lasern. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Garderobenmarke. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Schlange vor dem Club. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Kopfhörer. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Rave in einer Lagerhalle. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Toilettenschlange im Club. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Getränkebon. Ohne zu sprechen, die anderen raten.'),
('zeichnen','✏️ Zeichne: Taxi um 6 Uhr morgens. Ohne zu sprechen, die anderen raten.'),
('sound','🎵 Summe einen bekannten Song, die anderen erraten den Titel.'),
('sound','🎵 Mach 30 Sekunden eine Kickdrum mit dem Mund, ohne aus dem Takt zu kommen.'),
('sound','🎵 Imitiere einen Riser bis zum Drop, beim Drop müssen alle jubeln.'),
('sound','🎵 Summe ein Kinderlied als Techno-Version, die anderen erraten das Lied.'),
('sound','🎵 Mach nacheinander die Geräusche von Nebelmaschine, Strobo und Kickdrum.'),
('sound','🎵 Imitiere ein Geräusch aus dem Club, die anderen raten den Ort.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Wer länger auf einem Bein tanzt. Du musst gewinnen.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Schere, Stein, Papier, wer zuerst 2 Siege hat. Du musst gewinnen.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Abwechselnd Techno-Labels nennen, wer zuerst hängt, verliert. Du musst gewinnen.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Abwechselnd Getränke von der Clubkarte nennen, wer zuerst hängt, verliert. Du musst gewinnen.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Starrduell, wer zuerst lacht, verliert. Du musst gewinnen.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Wer schneller von 30 rückwärts zählt. Du musst gewinnen.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Abwechselnd DJs nennen, die mit dem gleichen Buchstaben anfangen. Die anderen wählen den Buchstaben. Du musst gewinnen.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Daumencatchen. Du musst gewinnen.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Wer zeigt den besseren Raver-Move? Die anderen stimmen ab. Du musst gewinnen.'),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Wer bleibt länger ernst, während der andere Grimassen zieht. Du musst gewinnen.'),
('dominik','🤯 Dominik: Wie net bezahlt?! Erfinde einen absurden Club-Eintritt.'),
('dominik','🤯 Dominik: Da kotzt er! Rede 15 Sekunden nur im Dialekt.'),
('dominik','🤯 Dominik: Erzähl, wie du heute Nacht an der Tür abgewiesen wurdest. Die anderen müssen lachen.'),
('dominik','🤯 Dominik: Mach die Ansage eines Türstehers, der eine Gruppe von 10 Leuten nicht reinlässt.'),
('dominik','🤯 Dominik: Verkauf den anderen eine leere Wasserflasche als VIP-Getränk.'),
('dominik','🤯 Dominik: Erfinde einen neuen Techno-Tanz und bring ihn allen bei.'),
('dominik','🤯 Dominik: Halte eine Dankesrede, als hättest du gerade den DJ-Award gewonnen.'),
('dominik','🤯 Dominik: Erklär, warum du schon um 23 Uhr im Club bist, ohne dass es peinlich klingt.')
on conflict (text) do nothing;

create or replace function public.party_circuit_land(p_room uuid, p_member uuid, p_total integer, p_info jsonb)
 returns void language plpgsql security definer set search_path to ''
as $function$
declare
  r public.party_rooms; m public.party_members; info jsonb := p_info;
  victim public.party_members; got int; pos int; t public.party_tasks;
begin
  select * into r from public.party_rooms where id = p_room;
  select * into m from public.party_members where id = p_member;
  pos := m.position;
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
  elsif pos in (4,20,24,36,48,52,68,72) then
    update public.party_rooms set roll = p_total, roll_info = info, phase = 'slf',
      timer_started_at = clock_timestamp(), slf_deadline = clock_timestamp() + interval '90 seconds',
      slf_letter = (array['A','B','D','E','F','G','H','K','L','M','N','P','R','S','T','W'])[floor(random()*16)::int + 1],
      task = 'Stadt Land Fluss' where id = r.id;
  elsif pos in (1,3,5,7,8,9,11,13,15,17,19,21,23,25,27,29,31,32,33,35,37,39,41,43,45,47,49,51,53,55,56,57,59,61,63,65,67,69,71,73,75,77,79) then
    select * into t from public.party_tasks where not (id = any(r.used_tasks)) order by random() limit 1;
    if not found then
      update public.party_rooms set used_tasks = '{}' where id = r.id;
      select * into t from public.party_tasks order by random() limit 1;
      r.used_tasks := '{}';
    end if;
    update public.party_rooms set roll = p_total, roll_info = info, phase = 'task',
      task = t.text, used_tasks = array_append(r.used_tasks, t.id), timer_started_at = null where id = r.id;
  elsif pos in (12,16,28,40,44,60,64,76) then
    perform public.party_circuit_card(r.id, m.id, 'aufgabe', p_total, info);
  elsif pos in (2,6,10,14,18,22,26,30,34,38,42,46,50,54,58,62,66,70,74,78) then
    perform public.party_circuit_card(r.id, m.id, 'ereignis', p_total, info);
  else
    raise exception 'Feld ohne Funktion: %', pos;
  end if;
end
$function$;

do $do$
declare d text; n text;
begin
  -- Würfeln: 80 Felder, VIP-Treppe auf 21 und 61
  d := pg_get_functiondef('public.party_circuit_roll'::regproc);
  n := replace(replace(replace(d, 'raw / 64', 'raw / 80'), 'raw % 64', 'raw % 80'), 'newpos in (20, 44)', 'newpos in (21, 61)');
  if n = d or n like '%64%' then raise exception 'party_circuit_roll unerwartet'; end if;
  execute n;
  -- Karten: Zielfeld bis 79, Stapel ohne Wiederholung
  d := pg_get_functiondef('public.party_circuit_card'::regproc);
  n := replace(d, 'least(63, m.position + c.value)', 'least(79, m.position + c.value)');
  n := replace(n, $a$select * into c from public.party_cards where deck = p_deck
    and title is distinct from (r.roll_info -> 'card' ->> 'title') order by random() limit 1;$a$,
  $b$select * into c from public.party_cards where deck = p_deck and not (id = any(r.used_cards)) order by random() limit 1;
  if not found then
    update public.party_rooms set used_cards = array(select x from unnest(used_cards) x where x not in (select id from public.party_cards where deck = p_deck)) where id = r.id;
    select * into c from public.party_cards where deck = p_deck order by random() limit 1;
  end if;
  update public.party_rooms set used_cards = array_append(used_cards, c.id) where id = r.id;$b$);
  if n not like '%used_cards%' or n like '%least(63%' then raise exception 'party_circuit_card unerwartet'; end if;
  execute n;
  -- VIP-Treppe im Rundkurs: kein Deckel mehr bei 63
  d := pg_get_functiondef('public.party_action'::regproc);
  n := replace(replace(d, 'position=least(63,position+6)', 'position=position+6'), 'least(63,m.position+6)', 'm.position+6');
  if n = d then raise exception 'party_action unerwartet'; end if;
  execute n;
end
$do$;
