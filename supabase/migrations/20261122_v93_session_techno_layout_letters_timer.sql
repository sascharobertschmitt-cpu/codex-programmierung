-- Build 9.3
-- 1) Felder pro Partie durchmischen (board_layout)
-- 2) SLF: Buchstaben wiederholen sich in einer Partie nicht, Kategorie Fluss -> Rauschmittel
-- 3) Aufgaben-Timer richtet sich nach der Aufgabe (10/15/20/30/60 s)
-- 4) Aufgabenkatalog: weniger generisch, mehr Session & Techno

-- ---------- Spalten ----------
alter table public.party_tasks add column if not exists seconds int not null default 60;
alter table public.party_rooms add column if not exists board_layout text;
alter table public.party_rooms add column if not exists used_letters text not null default '';

update public.party_tasks
   set seconds = least(120, greatest(5, (regexp_match(text, '(\d+) ?Sekunden'))[1]::int))
 where text ~ '\d+ ?Sekunden';

-- ---------- Felder-Layout ----------
-- Zeichen: S Start, F Ziel, L Stadt-Land-Fluss, A Aufgabe, E Ereignis, T Turbo (+3), D Umweg (-2)
create or replace function public.party_make_layout() returns text
language plpgsql volatile set search_path='' as $f$
declare arr text[]; i int; j int; t text; s text; tries int:=0;
begin
 loop
  tries:=tries+1;
  arr:=array_cat(array_cat(array_fill('L'::text,array[10]),array_fill('A'::text,array[28])),
                 array_cat(array_fill('E'::text,array[18]),array['T','T','T','D','D','D']));
  for i in reverse 62..2 loop
   j:=1+floor(random()*i)::int; t:=arr[i]; arr[i]:=arr[j]; arr[j]:=t;
  end loop;
  s:='S'||array_to_string(arr,'')||'F';
  -- SLF-Felder nie direkt hintereinander oder mit nur einem Feld Abstand
  exit when s !~ 'L.?L' or tries>500;
 end loop;
 return s;
end $f$;

-- altes festes Layout, fuer Partien die vor Build 9.3 gestartet wurden
create or replace function public.party_legacy_layout() returns text
language sql immutable set search_path='' as $f$
 select string_agg(case
   when n=0 then 'S' when n=63 then 'F'
   when n in (5,12,19,26,32,38,45,50,56,60) then 'L'
   when n in (2,4,6,9,11,13,16,18,20,22,25,27,30,33,35,37,39,42,44,46,48,51,53,55,57,59,61,62) then 'A'
   when n in (7,28,49) then 'T' when n in (17,40,58) then 'D'
   else 'E' end,'' order by n) from generate_series(0,63) n
$f$;

create or replace function public.party_task_seconds(p_text text) returns int
language sql stable security definer set search_path='' as $f$
 select coalesce((select seconds from public.party_tasks where text=p_text limit 1),60)
$f$;

-- ---------- Trigger: Layout + Buchstaben ohne Wiederholung ----------
create or replace function public.party_rooms_prep() returns trigger
language plpgsql set search_path='' as $f$
declare pool text[]:=array['A','B','D','E','F','G','H','K','L','M','N','P','R','S','T','W']; rest text[]; used text;
begin
 if new.status='playing' and old.status is distinct from 'playing' then
  new.used_letters:='';
  if coalesce(new.board_mode,'classic')<>'circuit' then new.board_layout:=public.party_make_layout(); end if;
 elsif new.status='lobby' then
  new.used_letters:=''; new.board_layout:=null;
 end if;
 if new.phase='slf' and old.phase is distinct from 'slf' then
  used:=coalesce(new.used_letters,'');
  select array_agg(l) into rest from unnest(pool) l where position(l in used)=0;
  if rest is null then used:=''; rest:=pool; end if;
  new.slf_letter:=rest[1+floor(random()*array_length(rest,1))::int];
  new.used_letters:=used||new.slf_letter;
 end if;
 return new;
end $f$;
drop trigger if exists party_rooms_prep on public.party_rooms;
create trigger party_rooms_prep before update on public.party_rooms for each row execute function public.party_rooms_prep();

-- ---------- Funktionen patchen ----------
create or replace function pg_temp.rep(d text, a text, b text) returns text language plpgsql as $f$
begin
 if position(a in d)=0 then raise exception 'Patch-Muster fehlt: %', a; end if;
 return replace(d,a,b);
end $f$;

do $do$
declare rec record; d text;
begin
 -- Kategorie Fluss -> Rauschmittel
 for rec in select oid from pg_proc where pronamespace='public'::regnamespace
   and proname in ('party_bot_tick','party_slf_draft','party_slf_finalize','party_slf_submit','party_slf_vote','party_snapshot')
 loop
  d:=pg_get_functiondef(rec.oid);
  if d like '%''Fluss''%' then d:=replace(d,'''Fluss''','''Rauschmittel'''); execute d; end if;
 end loop;

 -- Spielzug: Feldtyp aus dem Layout statt fester Listen
 d:=pg_get_functiondef('public.party_action(text,uuid,uuid,text)'::regprocedure);
 if d not like '%fk text%' then
  d:=pg_temp.rep(d,'declare r public.party_rooms; m public.party_members;','declare lay text; fk text; r public.party_rooms; m public.party_members;');
  d:=pg_temp.rep(d,'select least(63,position+dice) into newpos from public.party_members where id=m.id;',
    'select least(63,position+dice) into newpos from public.party_members where id=m.id; lay:=coalesce(r.board_layout,public.party_legacy_layout()); fk:=substr(lay,newpos+1,1);');
  d:=pg_temp.rep(d,'elsif newpos in (5,12,19,26,32,38,45,50,56,60) then','elsif fk=''L'' then');
  d:=pg_temp.rep(d,'elsif newpos in (2,4,6,9,11,13,16,18,20,22,25,27,30,33,35,37,39,42,44,46,48,51,53,55,57,59,61,62) then','elsif fk=''A'' then');
  d:=pg_temp.rep(d,'elsif newpos in (7,17,28,40,49,58) then','elsif fk in (''T'',''D'') then');
  d:=pg_temp.rep(d,'effect:=case when newpos in (7,28,49) then 3 else -2 end;','effect:=case when fk=''T'' then 3 else -2 end;');
  d:=pg_temp.rep(d,'elsif newpos in (1,3,8,10,14,15,21,23,24,29,31,34,36,41,43,47,52,54) then','elsif fk=''E'' then');
  d:=pg_temp.rep(d,'effect:=case when newpos%2=0 then 2 else -2 end;','effect:=case when random()<.5 then 2 else -2 end;');
  execute d;
 end if;

 -- Snapshot: Aufgaben-Timer pro Aufgabe + Layout ausliefern
 d:=pg_get_functiondef('public.party_snapshot(text,uuid)'::regprocedure);
 if d not like '%party_task_seconds%' then
  d:=pg_temp.rep(d,'interval ''60 seconds''','make_interval(secs=>public.party_task_seconds(r.task))');
  d:=pg_temp.rep(d,'''board_mode'',r.board_mode,','''board_mode'',r.board_mode,''board_layout'',coalesce(r.board_layout,public.party_legacy_layout()),''task_seconds'',public.party_task_seconds(r.task),');
  execute d;
 end if;
end $do$;

-- ---------- Rauschmittel statt Fluss ----------
delete from public.party_slf_lexicon where category='Fluss';
insert into public.party_slf_lexicon(category,term) values
('Rauschmittel','alkohol'),('Rauschmittel','absinth'),('Rauschmittel','amphetamin'),('Rauschmittel','aperol'),('Rauschmittel','amaretto'),('Rauschmittel','ayahuasca'),
('Rauschmittel','bier'),('Rauschmittel','bourbon'),('Rauschmittel','bowle'),('Rauschmittel','bacardi'),('Rauschmittel','brandy'),
('Rauschmittel','dmt'),('Rauschmittel','diazepam'),('Rauschmittel','doppelkorn'),('Rauschmittel','dextromethorphan'),
('Rauschmittel','ecstasy'),('Rauschmittel','energydrink'),('Rauschmittel','eierlikör'),('Rauschmittel','espresso'),('Rauschmittel','ephedrin'),
('Rauschmittel','fentanyl'),('Rauschmittel','fliegenpilz'),('Rauschmittel','fernet'),('Rauschmittel','fusel'),('Rauschmittel','flunitrazepam'),
('Rauschmittel','gras'),('Rauschmittel','gin'),('Rauschmittel','glühwein'),('Rauschmittel','ghb'),('Rauschmittel','grappa'),('Rauschmittel','genever'),
('Rauschmittel','haschisch'),('Rauschmittel','heroin'),('Rauschmittel','hanf'),('Rauschmittel','hugo'),('Rauschmittel','hustensaft'),
('Rauschmittel','koks'),('Rauschmittel','kokain'),('Rauschmittel','kaffee'),('Rauschmittel','ketamin'),('Rauschmittel','korn'),('Rauschmittel','kava'),('Rauschmittel','kautabak'),
('Rauschmittel','lsd'),('Rauschmittel','lachgas'),('Rauschmittel','likör'),('Rauschmittel','lambrusco'),('Rauschmittel','lean'),
('Rauschmittel','marihuana'),('Rauschmittel','mdma'),('Rauschmittel','meth'),('Rauschmittel','mate'),('Rauschmittel','morphin'),('Rauschmittel','mescalin'),('Rauschmittel','mojito'),('Rauschmittel','met'),
('Rauschmittel','nikotin'),('Rauschmittel','nitrazepam'),('Rauschmittel','nescafé'),('Rauschmittel','nikotinbeutel'),
('Rauschmittel','pilze'),('Rauschmittel','poppers'),('Rauschmittel','pervitin'),('Rauschmittel','pastis'),('Rauschmittel','prosecco'),('Rauschmittel','pfeffi'),('Rauschmittel','peyote'),('Rauschmittel','psilocybin'),
('Rauschmittel','rum'),('Rauschmittel','rotwein'),('Rauschmittel','ritalin'),('Rauschmittel','raki'),('Rauschmittel','rakija'),
('Rauschmittel','speed'),('Rauschmittel','schnaps'),('Rauschmittel','sekt'),('Rauschmittel','spice'),('Rauschmittel','shisha'),('Rauschmittel','snus'),('Rauschmittel','scotch'),('Rauschmittel','sake'),('Rauschmittel','sangria'),
('Rauschmittel','tabak'),('Rauschmittel','tequila'),('Rauschmittel','thc'),('Rauschmittel','tilidin'),('Rauschmittel','tramadol'),
('Rauschmittel','wodka'),('Rauschmittel','whisky'),('Rauschmittel','wein'),('Rauschmittel','weißwein'),('Rauschmittel','weed'),('Rauschmittel','wermut'),('Rauschmittel','wasserpfeife')
on conflict do nothing;

-- ---------- Aufgabenkatalog: generisches raus, Session & Techno rein ----------
delete from public.party_tasks
 where kind not in ('dominik','duell','sound')
   and text !~* '(dj|techno|bass|club|rave|drop|kick|beat|floor|session|afterhour|türsteher|vinyl|nebel|garderobe|loop|bpm|laser|synth|festival|kater|strobo|discokugel|plattenspieler|nachtleben|warteschlange)';

insert into public.party_tasks(kind,text,seconds) values
('pantomime','🎭 Pantomime: Ein DJ merkt beim Drop, dass der falsche Track läuft. Die anderen raten.',60),
('pantomime','🎭 Pantomime: Ein Raver kratzt um 6 Uhr morgens seine letzte Energie für den Floor zusammen.',60),
('pantomime','🎭 Pantomime: Jemand steht in der Schlange vorm Club und bereitet sich auf das Türsteher-Verhör vor.',60),
('pantomime','🎭 Pantomime: Ein DJ lässt beim Plattenwechsel die Nadel fallen und tut so, als wäre es Absicht.',60),
('pantomime','🎭 Pantomime: Jemand sucht im dunklen Club sein klingelndes Handy.',60),
('pantomime','🎭 Pantomime: Ein Barkeeper bedient drei Gäste gleichzeitig, während der Bass die Gläser tanzen lässt.',60),
('pantomime','🎭 Pantomime: Jemand sieht bei der Afterhour um 11 Uhr morgens die Sonne und glaubt es nicht.',60),
('pantomime','🎭 Pantomime: Ein Tontechniker dreht den Bass auf und plötzlich pfeift alles vor Rückkopplung.',60),
('pantomime','🎭 Pantomime: Du willst deinen Kumpel nur mit Handzeichen überreden, endlich nach Hause zu gehen.',60),
('pantomime','🎭 Pantomime: Ein DJ klemmt die Kopfhörer an die Schulter und bedient den Crossfader mit dem Ellbogen.',60),
('pantomime','🎭 Pantomime: Jemand mit Ohrstöpseln tut so, als würde er sein Gegenüber verstehen.',60),
('pantomime','🎭 Pantomime: Ein Fotograf klebt Gästen die Handykameras zu, weil im Club nicht gefilmt wird.',60),
('pantomime','🎭 Pantomime: Jemand springt vom Podest in die Menge und merkt, dass niemand fängt.',60),
('pantomime','🎭 Pantomime: Jemand versucht, im Takt von 140 BPM Zähne zu putzen.',60),
('pantomime','🎭 Pantomime: Ein Synth-Nerd führt stolz sein Modular-Rack mit 200 Kabeln vor.',60),
('pantomime','🎭 Pantomime: Ein Raver tanzt auf der Stelle und merkt nach 10 Stunden, dass nur noch er auf dem Floor ist.',60),
('pantomime','🎭 Pantomime: Ein DJ legt zum ersten Mal in einem leeren Club auf und tut so, als wäre er der Headliner.',60),
('pantomime','🎭 Pantomime: Jemand wartet an der Garderobe um 5 Uhr morgens auf seine Jacke.',60),
('pantomime','🎭 Pantomime: Ein Nachbar um 4 Uhr nachts: Er will sich über den Lärm beschweren, wippt aber unfreiwillig im Takt mit.',60),
('pantomime','🎭 Pantomime: Ein Festivalgänger baut sein Zelt im Regen auf, während im Hintergrund der Bass wummert.',60),
('erklaeren','🗣️ Erkläre „Drop“, ohne Bass, Musik oder Beat zu sagen.',60),
('erklaeren','🗣️ Erkläre „Warteschlange vorm Club“, ohne Türsteher, Einlass oder Stehen zu sagen.',60),
('erklaeren','🗣️ Erkläre „Kickdrum“, ohne Bass, Trommel oder Fuß zu sagen.',60),
('erklaeren','🗣️ Erkläre „Crossfader“, ohne DJ, Regler oder Mischpult zu sagen.',60),
('erklaeren','🗣️ Erkläre „Vinyl“, ohne Platte, Schallplatte oder Nadel zu sagen.',60),
('erklaeren','🗣️ Erkläre „Loop“, ohne Wiederholung, Schleife oder Endlos zu sagen.',60),
('erklaeren','🗣️ Erkläre „Stroboskop“, ohne Licht, Blitz oder Flackern zu sagen.',60),
('erklaeren','🗣️ Erkläre „Hi-Hat“, ohne Schlagzeug, Becken oder Zischen zu sagen.',60),
('erklaeren','🗣️ Erkläre „Pre-Drinks“, ohne Alkohol, vorher oder Wohnung zu sagen.',60),
('erklaeren','🗣️ Erkläre „Mate“, ohne Getränk, Flasche oder Koffein zu sagen.',60),
('erklaeren','🗣️ Erkläre „Ohrstöpsel“, ohne Ohr, Lärm oder Schutz zu sagen.',60),
('erklaeren','🗣️ Erkläre „Garderobenmarke“, ohne Jacke, Nummer oder abgeben zu sagen.',60),
('erklaeren','🗣️ Erkläre „Backstage“, ohne Bühne, hinten oder Künstler zu sagen.',60),
('erklaeren','🗣️ Erkläre „Soundcheck“, ohne Mikrofon, Test oder Eins-Zwei zu sagen.',60),
('erklaeren','🗣️ Erkläre „Sunrise-Set“, ohne Sonne, Morgen oder DJ zu sagen.',60),
('erklaeren','🗣️ Erkläre „Tinnitus“, ohne Ohr, Pfeifen oder laut zu sagen.',60),
('erklaeren','🗣️ Erkläre „Rave“, ohne Techno, Party oder Tanzen zu sagen.',60),
('erklaeren','🗣️ Erkläre „Subwoofer“, ohne Bass, Box oder Lautsprecher zu sagen.',60),
('erklaeren','🗣️ Erkläre „Festivalbändchen“, ohne Arm, Eintritt oder Festival zu sagen.',60),
('erklaeren','🗣️ Erkläre „Warm-up-Set“, ohne DJ, Anfang oder früh zu sagen.',60),
('zeichnen','✏️ Zeichne einen Club von außen, vor dem die Schlange drei Stunden lang ist. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne das Innere eines Clubs um 7 Uhr morgens. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne ein Modular-Synthesizer-Rack mit Kabelsalat. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne einen Raver mit Sonnenbrille um 6 Uhr morgens. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne ein Stroboskop-Gewitter in einem Keller. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne einen Subwoofer, der eine ganze Wand zum Wackeln bringt. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne einen Kater am Montag: Die Bassdrum hallt im Kopf nach. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne das Cover eines Techno-Albums aus nur drei Formen. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne ein Festivalzelt-Lager nach drei Tagen Regen. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne eine Schallplatte mit Schluckauf. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne eine Warteschlange vor dem Club, von der nur die Schuhe zu sehen sind. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne einen Türsteher als Berg. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne den Sonnenaufgang auf dem Floor mit müden Tänzern. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne eine Garderobe, die kurz vor dem Einsturz steht. Ohne zu sprechen.',60),
('zeichnen','✏️ Zeichne einen DJ-Controller mit allen Reglern, an die du dich erinnerst. Ohne zu sprechen.',60),
('fun','🤪 Halte 20 Sekunden lang als Türsteher eine Ansage: Warum kommt heute Nacht niemand mehr rein?',20),
('fun','🤪 Moderiere 20 Sekunden lang einen Techno-Track wie einen Wetterbericht: „Heute 140 BPM, Böen im Bassbereich.“',20),
('fun','🤪 Tanze 15 Sekunden lang zu einem imaginären Track mit 150 BPM, ohne den Takt zu verlieren.',15),
('fun','🤪 Beschreibe 20 Sekunden lang deinen Lieblingstrack wie bei einer Weinverkostung.',20),
('fun','🤪 Erfinde in 20 Sekunden einen Techno-DJ-Namen samt Tourdaten.',20),
('fun','🤪 Halte 20 Sekunden lang eine Rede als Veranstalter, warum die Afterhour bis Dienstag geht.',20),
('fun','🤪 Mixe 15 Sekunden lang mit maximalem Ernst imaginär auf zwei Plattenspielern. Die anderen müssen ernst bleiben.',15),
('fun','🤪 Erkläre 20 Sekunden lang deiner Oma, was ein Drop ist.',20),
('fun','🤪 Berichte 20 Sekunden lang als Reporter live aus der Schlange vor dem Club.',20),
('fun','🤪 Erzähle 20 Sekunden lang eine Kater-Geschichte. Wahr oder erfunden? Die anderen raten.',20),
('fun','🤪 Sprich 15 Sekunden lang nur in Bassdrum-Silben („Bum, Tss, Bum, Tss“) und tu so, als würdest du etwas Wichtiges sagen.',15),
('fun','🤪 Präsentiere 20 Sekunden lang dein neues Album „Kellerkind“ mit Tracklist.',20),
('fun','🤪 Mach 20 Sekunden lang eine Security-Durchsage: „Bitte nicht auf den Subwoofer klettern“ mit steigender Dramatik.',20),
('fun','🤪 Überzeuge die anderen in 30 Sekunden, dass Montagmorgen der beste Zeitpunkt für eine Session ist.',30),
('fun','🤪 Spiele 20 Sekunden lang einen Barkeeper, der Getränke nur mit Techno-Begriffen bestellt.',20),
('fun','🤪 Tu 20 Sekunden lang so, als wärst du ein Synthesizer, der hochgefahren wird. Mit Geräuschen.',20),
('fun','🤪 Gib 20 Sekunden lang ein Interview als DJ nach dem Set. Die anderen stellen die Fragen.',20),
('fun','🤪 Gib 30 Sekunden lang Tipps, wie man eine 12-Stunden-Session übersteht.',30),
('fun','🤪 Halte einen 20-sekündigen Toast auf den Bass.',20),
('fun','🤪 Spiele 15 Sekunden lang eine Nebelmaschine, die gerade kaputtgeht.',15),
('fun','🤪 Du baust 30 Sekunden lang einen Riser. Die anderen steigern sich mit dir und müssen beim Drop gemeinsam explodieren.',30),
('fun','🤪 Verteidige 20 Sekunden lang, warum der letzte Track des Abends 45 Minuten dauern muss.',20),
('fun','🤪 Verkaufe 20 Sekunden lang einem DJ einen Plattenspieler, der nur Schlager abspielt.',20),
('fun','🤪 Beschreibe 20 Sekunden lang den perfekten Floor mit allen Details: Licht, Bass, Menschen.',20),
('fun','🤪 Zähle 15 Sekunden lang rückwärts von 16 im Takt einer imaginären Kickdrum.',15),
('quiz','🧠 Nenne in 20 Sekunden 5 Techno-Genres oder Stilrichtungen.',20),
('quiz','🧠 Nenne in 20 Sekunden 5 Techno-Clubs auf der Welt.',20),
('quiz','🧠 Nenne in 20 Sekunden 5 Dinge, die zu einem DJ-Setup gehören.',20),
('quiz','🧠 Nenne in 20 Sekunden 5 bekannte Techno-DJs oder Producer.',20),
('quiz','🧠 Nenne in 15 Sekunden 5 alkoholfreie Getränke für eine lange Session.',15),
('quiz','🧠 Nenne in 30 Sekunden 8 Wörter, die „Bass“ oder „Beat“ enthalten.',30),
('quiz','🧠 Nenne in 20 Sekunden 5 Safer-Party-Regeln.',20),
('quiz','🧠 Nenne in 20 Sekunden 5 Instrumente oder Geräte, die man in elektronischer Musik braucht.',20),
('quiz','🧠 Nenne in 20 Sekunden 6 Dinge, die auf dem Rider eines DJs stehen könnten.',20),
('quiz','🧠 Nenne in 20 Sekunden 5 Songs mit „Night“ oder „Nacht“ im Titel.',20),
('quiz','🧠 Nenne in 20 Sekunden 5 Dinge, die man auf der Afterhour um 9 Uhr morgens braucht.',20),
('quiz','🧠 Nenne in 20 Sekunden 6 Wörter für „Kater“ oder „völlig fertig am nächsten Tag“.',20),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Wer klopft länger einen sauberen Four-on-the-Floor-Takt auf den Tisch? Du musst gewinnen.',60),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Abwechselnd Techno-Tracks nennen, wer zuerst hängt, verliert. Du musst gewinnen.',60),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Wer baut den besseren Riser mit dem Mund bis zum Drop? Die anderen stimmen ab. Du musst gewinnen.',60),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Wer hält länger die Planke, während der andere Techno-Begriffe aufzählt? Du musst gewinnen.',60),
('duell','⚔️ Duell gegen einen Mitspieler deiner Wahl: Abwechselnd Wörter mit „Bass“ bilden, wer zuerst hängt, verliert. Du musst gewinnen.',60),
('sound','🎵 Mach 15 Sekunden lang eine Hi-Hat mit dem Mund auf dem Offbeat, ohne dich zu verhaspeln.',15),
('sound','🎵 Beatboxe 20 Sekunden lang vier Takte Four-on-the-Floor mit Clap und Hi-Hat.',20),
('sound','🎵 Mach das Geräusch eines Subwoofers, der kurz vor dem Platzen ist. Die anderen raten.',60),
('sound','🎵 Summe einen bekannten Song im Techno-Tempo von 130 BPM. Die anderen erraten den Titel.',60),
('sound','🎵 Imitiere eine Schallplatte, die rückwärts gescratcht wird. Die anderen raten.',60)
on conflict (text) do nothing;
