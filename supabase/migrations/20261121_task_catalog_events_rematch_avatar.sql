insert into public.party_tasks(kind,text) values
('pantomime','🎭 Pantomime: Du bist ein Pinguin, der versucht, auf Glatteis Pizza zu bestellen.'),
('pantomime','🎭 Pantomime: Eine Katze, die zum ersten Mal Staubsauger sieht.'),
('pantomime','🎭 Pantomime: Jemand, der merkt, dass er seit zehn Minuten den falschen Einkaufswagen schiebt.'),
('pantomime','🎭 Pantomime: Opa versucht, WLAN zu reparieren.'),
('pantomime','🎭 Pantomime: Ein Hund, der Gassi geht und seinen Menschen hinter sich herzieht.'),
('pantomime','🎭 Pantomime: Ein Roboter, dem mitten im Tanz der Akku ausgeht.'),
('pantomime','🎭 Pantomime: Jemand, der im Aufzug furzt und so tut, als wäre nichts.'),
('pantomime','🎭 Pantomime: Ein Superheld, der keine Superkraft mehr hat, aber das niemand wissen soll.'),
('pantomime','🎭 Pantomime: Ein Koch, der mit einer Wespe in der Küche kämpft.'),
('pantomime','🎭 Pantomime: Ein Hahn am frühen Morgen mit schlimmem Kater.'),
('pantomime','🎭 Pantomime: Eine Giraffe, die durch eine Tür zu kleiner Höhe will.'),
('pantomime','🎭 Pantomime: Ein Türsteher, der die eigene Mama nicht reinlassen darf.'),
('pantomime','🎭 Pantomime: Ein DJ, bei dem der USB-Stick leer ist.'),
('pantomime','🎭 Pantomime: Ein Fußballer, der nach einem Foul den Oscar gewinnen will.'),
('erklaeren','🗣️ Erkläre „Zahnbürste“, ohne Zahn, Bürste oder Putzen zu sagen.'),
('erklaeren','🗣️ Erkläre „Mikrowelle“, ohne Essen, Warm oder Strahlen zu sagen.'),
('erklaeren','🗣️ Erkläre „Schwiegermutter“, ohne Ehe, Mutter oder Familie zu sagen.'),
('erklaeren','🗣️ Erkläre „Montag“, ohne Woche, Arbeit oder Wochenende zu sagen.'),
('erklaeren','🗣️ Erkläre „Döner“, ohne Fleisch, Türkei oder Brot zu sagen.'),
('erklaeren','🗣️ Erkläre „Kater“, ohne Alkohol, Tier oder Kopfschmerzen zu sagen.'),
('erklaeren','🗣️ Erkläre „Navi“, ohne Auto, Straße oder Weg zu sagen.'),
('erklaeren','🗣️ Erkläre „Sonnenbrille“, ohne Sonne, Auge oder Brille zu sagen.'),
('erklaeren','🗣️ Erkläre „Dönerteller“, ohne Essen, Teller oder Soße zu sagen.'),
('erklaeren','🗣️ Erkläre „Handyakku“, ohne Telefon, Strom oder Laden zu sagen.'),
('erklaeren','🗣️ Erkläre „Eiffelturm“, ohne Paris, Frankreich oder Turm zu sagen.'),
('erklaeren','🗣️ Erkläre „Waschmaschine“, ohne Wäsche, Wasser oder Socken zu sagen.'),
('zeichnen','✏️ Zeichne einen Hund, der Skateboard fährt. Die anderen raten – du darfst nicht sprechen.'),
('zeichnen','✏️ Zeichne eine Pizza mit möglichst vielen Gesichtern – ohne zu sprechen.'),
('zeichnen','✏️ Zeichne dein Lieblingstier mit einem Hut. Ohne Worte!'),
('zeichnen','✏️ Zeichne ein Raumschiff, das gerade Parkplatzprobleme hat.'),
('zeichnen','✏️ Zeichne eine Schnecke auf der Flucht. Kein Wort!'),
('zeichnen','✏️ Zeichne einen Kühlschrank von innen, wenn Single-Männer kochen.'),
('zeichnen','✏️ Zeichne ein Gespenst mit Kater. Ohne Sprechen.'),
('zeichnen','✏️ Zeichne einen Bagger, der Eis isst. Nur zeichnen!'),
('zeichnen','✏️ Zeichne mit geschlossenen Augen einen Elefanten. Die anderen raten.'),
('fun','🤪 Sprich 20 Sekunden lang nur im Ton eines Nachrichtensprechers über dein Frühstück.'),
('fun','🤪 Erzähle einen Witz. Wenn niemand lacht, musst du ihn nochmal erzählen – mit Kunstpause.'),
('fun','🤪 Sing „Alle meine Entchen“ im Stil von Opernsängern.'),
('fun','🤪 Lies die letzte Nachricht auf deinem Handy mit Gänsehaut-Stimme vor (gern auch gekürzt).'),
('fun','🤪 Rede 20 Sekunden wie ein Fußballkommentator über das, was gerade im Raum passiert.'),
('fun','🤪 Mach 10 Sekunden lang deinen besten Roboter-Tanz.'),
('fun','🤪 Beschreibe den Mitspieler links von dir als wäre er ein Tierdokumentations-Tier.'),
('fun','🤪 Nenne in 15 Sekunden 8 Dinge, die man nicht in den Koffer packen sollte.'),
('fun','🤪 Verkaufe den anderen deinen Schuh, als wäre es ein Luxusprodukt.'),
('fun','🤪 Sprich 15 Sekunden lang nur in Fragen. Wer einen Satz ohne Fragezeichen sagt, verliert.'),
('fun','🤪 Mach Geräusche von 5 Tieren – die anderen raten.'),
('fun','🤪 Halte eine Dankesrede für einen Oscar, den du für „Besten Statisten im eigenen Leben“ gewinnst.'),
('fun','🤪 Erfinde in 20 Sekunden einen neuen Tanz und gib ihm einen Namen.'),
('fun','🤪 Mach 15 Sekunden lang Werbung für ein Produkt, das niemand braucht: Bio-Wasser ohne Wasser.'),
('fun','🤪 Sprich einen kompletten Satz, ohne den Buchstaben „E“ zu benutzen.'),
('fun','🤪 Dominik: Wie net bezahlt?! Erfinde einen absurden Club-Eintritt und verteidige ihn.'),
('fun','🤪 Dominik: Da kotzt er! Rede 15 Sekunden nur im Dialekt.'),
('fun','🎭 Pantomime: Stelle einen DJ ohne Strom dar.')
on conflict (text) do nothing;

create or replace function public.party_pick_task(p_room uuid) returns text
language plpgsql security definer set search_path='' as $f$
declare t public.party_tasks; used int[];
begin
 select coalesce(used_tasks,'{}') into used from public.party_rooms where id=p_room;
 select * into t from public.party_tasks where not (id = any(used)) order by random() limit 1;
 if not found then used:='{}'; select * into t from public.party_tasks order by random() limit 1; end if;
 update public.party_rooms set used_tasks=used||t.id where id=p_room;
 return t.text;
end $f$;

CREATE OR REPLACE FUNCTION public.party_action(p_code text, p_token uuid, p_host_token uuid, p_action text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare r public.party_rooms; m public.party_members; n int; idx int; dice int; judge_idx int; newpos int; effect int; event_text text; picked text; choices text[]:=array['🎭 Pantomime: Stelle eine Discokugel dar','🎭 Pantomime: Stelle einen DJ ohne Strom dar','🗣️ Erkläre Afterhour ohne Party, Morgen oder Feiern','✏️ Zeichne eine Nebelmaschine auf Papier','🤯 Dominik: Wie net bezahlt?! Erfinde einen absurden Club-Eintritt','🤯 Dominik: Da kotzt er! Rede 15 Sekunden nur im Dialekt'];
begin
select * into r from public.party_rooms where code=upper(trim(p_code)) for update;
if not found then raise exception 'Lobby fehlt'; end if;
select * into m from public.party_members where room_id=r.id and token=p_token;
if not found then raise exception 'Kein Zugang'; end if;
select count(*) into n from public.party_members where room_id=r.id;
select ord-1 into idx from (select id,row_number() over(order by joined_at,id) ord from public.party_members where room_id=r.id) x where id=m.id;
if p_action in ('start_circuit','start_circuit_3') then
if r.host_token is distinct from p_host_token then raise exception 'Nur Host kann starten'; end if;
if n<2 then raise exception 'Mindestens zwei Spieler'; end if;
if r.status<>'lobby' then raise exception 'Spiel bereits gestartet'; end if;
update public.party_members set position=0,lap=0,cash=0,skip=false,stars=0,points=0,vip=0,turbo=false where room_id=r.id;
update public.party_rooms set status='playing',phase='ready',turn_index=0,timer_started_at=null,board_mode='circuit',laps=3,roll_info=null,ending_at=null,star_field=null,used_tasks='{}',used_cards='{}' where id=r.id;
elsif p_action='start' then
if r.host_token is distinct from p_host_token then raise exception 'Nur Host kann starten'; end if;
if n<2 then raise exception 'Mindestens zwei Spieler'; end if;
if r.status<>'lobby' then raise exception 'Spiel bereits gestartet'; end if;
update public.party_rooms set status='playing',phase='ready',turn_index=0,timer_started_at=null where id=r.id;
elsif p_action='roll' then
if r.status<>'playing' or r.phase<>'ready' or idx<>(r.turn_index%n) then raise exception 'Nicht dein Zug'; end if;
if r.board_mode='circuit' then perform public.party_circuit_roll(r.id,m.id); return public.party_snapshot(p_code,p_token); end if;
dice:=floor(random()*6)::int+1;
select least(63,position+dice) into newpos from public.party_members where id=m.id;
update public.party_members set position=newpos where id=m.id;
if newpos=63 then
update public.party_rooms set roll=dice,status='finished',phase='finished',task='🏆 ' || m.name || ' hat das Ziel erreicht!',timer_started_at=null where id=r.id;
elsif newpos in (5,12,19,26,32,38,45,50,56,60) then
update public.party_rooms set roll=dice,phase='slf',timer_started_at=clock_timestamp(),slf_deadline=clock_timestamp()+interval '90 seconds',slf_letter=(array['A','B','D','E','F','G','H','K','L','M','N','P','R','S','T','W'])[floor(random()*16)::int+1],task='Stadt Land Fluss' where id=r.id;
elsif newpos in (2,4,6,9,11,13,16,18,20,22,25,27,30,33,35,37,39,42,44,46,48,51,53,55,57,59,61,62) then
picked:=public.party_pick_task(r.id);
update public.party_rooms set roll=dice,phase='task',task=picked,timer_started_at=null where id=r.id;
elsif newpos in (7,17,28,40,49,58) then
effect:=case when newpos in (7,28,49) then 3 else -2 end;
update public.party_members set position=greatest(0,least(62,newpos+effect)) where id=m.id;
event_text:=case when effect>0 then '🎲 Spezial: Turbo! 3 Felder vor.' else '🎲 Spezial: Umweg! 2 Felder zurück.' end;
update public.party_rooms set roll=dice,phase='event',task=event_text,timer_started_at=null where id=r.id;
elsif newpos in (1,3,8,10,14,15,21,23,24,29,31,34,36,41,43,47,52,54) then
effect:=case when newpos%2=0 then 2 else -2 end;
update public.party_members set position=greatest(0,least(62,newpos+effect)) where id=m.id;
event_text:=case when effect>0 then (array['⚡ Rückenwind! Der DJ dreht auf – 2 Felder vor.','⚡ Freibier an der Bar! Du tanzt 2 Felder nach vorn.','⚡ Der Türsteher kennt dich. VIP-Abkürzung: 2 Felder vor.','⚡ Ein Fremder gibt dir einen Shot Energie. 2 Felder vor!','⚡ Dein Lieblingslied läuft. Du schwebst 2 Felder vor.','⚡ Du findest 10 Euro auf dem Boden und rennst 2 Felder vor.','⚡ Taxi gefunden! 2 Felder vor.','⚡ Konfettikanone! Der Schwung trägt dich 2 Felder nach vorn.'])[floor(random()*8)::int+1] else (array['⚡ Rückschlag! Du bist in eine Pfütze getreten – 2 Felder zurück.','⚡ Dein Handy ist leer und du hast dich verlaufen. 2 Felder zurück.','⚡ Jemand hat dein Getränk umgekippt. Du gehst 2 Felder zurück, um Ersatz zu holen.','⚡ Der Ex läuft vorbei! Du drehst 2 Felder zurück.','⚡ Schuhbändel offen. Sturz! 2 Felder zurück.','⚡ Die Garderobennummer ist weg. Du suchst 2 Felder zurück.','⚡ Der Bass war zu laut, du musst kurz raus. 2 Felder zurück.','⚡ Kater-Vorbote: Du schleichst 2 Felder zurück.'])[floor(random()*8)::int+1] end;
update public.party_rooms set roll=dice,phase='event',task=event_text,timer_started_at=null where id=r.id;
else raise exception 'Feld ohne Funktion: %',newpos;
end if;
elsif p_action in ('buy_turbo','buy_vip') then
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
elsif p_action in ('star_yes','star_no') then
if r.phase<>'choice' or not (coalesce(r.roll_info,'{}'::jsonb) ? 'star_offer') then raise exception 'Kein Sternkauf offen'; end if;
if idx<>(r.turn_index%n) then raise exception 'Nur der aktive Spieler entscheidet'; end if;
perform public.party_circuit_star(r.id,m.id,p_action='star_yes');
elsif p_action in ('stairs_yes','stairs_no') then
if r.phase<>'choice' or r.status<>'playing' then raise exception 'Keine Entscheidung offen'; end if;
if idx<>(r.turn_index%n) then raise exception 'Nur der aktive Spieler entscheidet'; end if;
if p_action='stairs_yes' and m.cash>=100 then
update public.party_members set cash=cash-100,position=position+6 where id=m.id;
perform public.party_circuit_land(r.id,m.id,r.roll,r.roll_info||jsonb_build_object('stairs_used',true,'to',m.position+6));
else
perform public.party_circuit_land(r.id,m.id,r.roll,r.roll_info||jsonb_build_object('stairs_used',false));
end if;
elsif p_action='event_next' then
if r.phase<>'event' or r.status<>'playing' then raise exception 'Kein Ereignis aktiv'; end if;
if idx<>(r.turn_index%n) and r.host_token is distinct from p_host_token then raise exception 'Nur aktiver Spieler oder Host'; end if;
update public.party_rooms set phase='ready',turn_index=turn_index+1,task=null where id=r.id;
elsif p_action='slf_stop' then
if r.phase<>'slf' or r.status<>'playing' then raise exception 'Keine aktive Runde'; end if;
update public.party_rooms set slf_deadline=least(r.slf_deadline,clock_timestamp()+interval '3 seconds') where id=r.id;
elsif p_action='slf_finish' then
if r.phase<>'slf' or r.status<>'playing' then raise exception 'Keine aktive Runde'; end if;

if clock_timestamp()<r.slf_deadline and (select count(*) from public.party_slf_answers where room_id=r.id and turn_index=r.turn_index and submitted=true)<n then raise exception 'Runde läuft'; end if;
update public.party_rooms set phase='slf_review',task='Stadt–Land–Fluss: Begriffe prüfen',timer_started_at=null where id=r.id;
elsif p_action='slf_next' then
if r.phase<>'slf_results' then raise exception 'Prüfung noch nicht abgeschlossen'; end if;
-- Any player can return to the board after all votes.
update public.party_rooms set phase='ready',turn_index=turn_index+1,task=null,slf_deadline=null where id=r.id;
elsif p_action='timer' then
if r.status<>'playing' or r.phase<>'task' or idx<>(r.turn_index%n) then raise exception 'Nur der aktive Spieler kann den Timer starten'; end if;
if r.timer_started_at is null then update public.party_rooms set timer_started_at=clock_timestamp() where id=r.id; end if;
elsif p_action='cancel' then
if r.status<>'playing' or r.phase<>'task' then raise exception 'Keine Aufgabe aktiv'; end if;
if idx<>(r.turn_index%n) and r.host_token is distinct from p_host_token then raise exception 'Nur aktiver Spieler oder Host kann abbrechen'; end if;
if r.timer_started_at is null then raise exception 'Aufgabe wurde noch nicht gestartet'; end if;
update public.party_rooms set phase='ready',turn_index=turn_index+1,task=null,timer_started_at=null where id=r.id;
elsif p_action in ('success','fail') then
if r.status<>'playing' or r.phase<>'task' then raise exception 'Keine Aufgabe zu bewerten'; end if;
judge_idx:=(r.turn_index+1)%n;
if idx<>judge_idx and not (idx=(r.turn_index%n) and coalesce((select pm.is_bot from public.party_members pm where pm.room_id=r.id order by pm.joined_at,pm.id offset judge_idx limit 1),false)) then raise exception 'Nur der andere Spieler darf bewerten'; end if;
if r.timer_started_at is null then raise exception 'Aufgabe wurde noch nicht gestartet'; end if;
if p_action='success' then
update public.party_members set points=points+10 where id=(select id from public.party_members where room_id=r.id order by joined_at,id offset (r.turn_index%n) limit 1);
if r.board_mode='circuit' and r.roll_info->'card'->>'deck'='aufgabe' then
update public.party_members set cash=cash+coalesce((r.roll_info->'card'->>'value')::int,0) where id=(select id from public.party_members where room_id=r.id order by joined_at,id offset (r.turn_index%n) limit 1);
end if;
end if;
update public.party_rooms set phase='ready',turn_index=turn_index+1,task=null,timer_started_at=null where id=r.id;
elsif p_action='rematch' then
if r.status<>'finished' then raise exception 'Spiel läuft noch'; end if;
delete from public.party_slf_votes where room_id=r.id;
delete from public.party_slf_answers where room_id=r.id;
update public.party_members set position=0,lap=0,cash=0,skip=false,stars=0,points=0,vip=0,turbo=false where room_id=r.id;
update public.party_rooms set status='lobby',phase='lobby',turn_index=0,roll=null,task=null,timer_started_at=null,slf_letter=null,slf_deadline=null,roll_info=null,ending_at=null,star_field=null,used_tasks='{}',used_cards='{}' where id=r.id;
else raise exception 'Unbekannte Aktion'; end if;
return public.party_snapshot(p_code,p_token);
end $function$;

-- ===== Spieler-Avatare (frei konfigurierbare 3D-Figur) =====
alter table public.party_members add column if not exists avatar text;

CREATE OR REPLACE FUNCTION public.party_snapshot(p_code text, p_token uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare r public.party_rooms;m public.party_members;arr jsonb;active_player uuid;judge_player uuid;player_count int;submitted int;mine boolean;slf_results jsonb;slf_round jsonb;
begin
select * into r from public.party_rooms where code=upper(trim(p_code));
if found and r.status='playing' and r.phase='task' and r.timer_started_at is not null and r.timer_started_at + interval '60 seconds' <= clock_timestamp() then
update public.party_rooms set phase='ready',turn_index=turn_index+1,task=null,timer_started_at=null where id=r.id and phase='task' and timer_started_at + interval '60 seconds' <= clock_timestamp();
select * into r from public.party_rooms where id=r.id;
end if;
if not found then raise exception 'Lobby nicht gefunden'; end if;
if r.status='playing' and r.phase='slf' and (r.slf_deadline<=clock_timestamp() or (select count(*) from public.party_slf_answers sa where sa.room_id=r.id and sa.turn_index=r.turn_index and sa.submitted=true)=(select count(*) from public.party_members where room_id=r.id)) then
perform 1 from public.party_rooms where id=r.id for update;
select * into r from public.party_rooms where id=r.id;
if r.phase='slf' and (r.slf_deadline<=clock_timestamp() or (select count(*) from public.party_slf_answers sa where sa.room_id=r.id and sa.turn_index=r.turn_index and sa.submitted=true)=(select count(*) from public.party_members where room_id=r.id)) then
update public.party_rooms set phase='slf_review',task='Stadt–Land–Fluss: Begriffe prüfen' where id=r.id;
select * into r from public.party_rooms where id=r.id;
end if;
end if;
select * into m from public.party_members where room_id=r.id and token=p_token;
if not found then raise exception 'Kein Zugang'; end if;
select coalesce(jsonb_agg(jsonb_build_object('id',id,'name',name,'position',position,'points',points,'lap',lap,'cash',cash,'skip',skip,'is_bot',is_bot,'hat',hat,'avatar',avatar,'vip',vip,'turbo',turbo,'stars',stars) order by joined_at,id),'[]'::jsonb),count(*) into arr,player_count from public.party_members where room_id=r.id;
select id into active_player from public.party_members where room_id=r.id order by joined_at,id offset (r.turn_index % greatest(player_count,1)) limit 1;
select id into judge_player from public.party_members where room_id=r.id order by joined_at,id offset ((r.turn_index+1) % greatest(player_count,1)) limit 1;
select count(*),coalesce(bool_or(player_id=m.id),false) into submitted,mine from public.party_slf_answers sa where sa.room_id=r.id and sa.turn_index=r.turn_index and sa.submitted=true;
select coalesce(jsonb_agg(jsonb_build_object('id',p.id,'name',p.name,'answers',coalesce(a.answers,'{}'::jsonb),'points',p.points,'round_points',coalesce((select sum(case when a.answers is null or not public.party_slf_approved(r.id,r.turn_index,p.id,k.key,r.slf_letter,a.answers->>k.key) then 0 when (select count(distinct v.player_id) from public.party_slf_answers v where v.room_id=r.id and v.turn_index=r.turn_index and public.party_slf_approved(r.id,r.turn_index,v.player_id,k.key,r.slf_letter,v.answers->>k.key))=1 then 20 when (select count(*) from public.party_slf_answers v where v.room_id=r.id and v.turn_index=r.turn_index and public.party_slf_approved(r.id,r.turn_index,v.player_id,k.key,r.slf_letter,v.answers->>k.key) and lower(trim(v.answers->>k.key))=lower(trim(a.answers->>k.key)))>1 then 5 else 10 end) from (select unnest(array['Stadt','Land','Fluss','Tier','Beruf']) key) k),0),'category_points',(select jsonb_object_agg(k.key,case when a.answers is null or not public.party_slf_approved(r.id,r.turn_index,p.id,k.key,r.slf_letter,a.answers->>k.key) then 0 when (select count(distinct v.player_id) from public.party_slf_answers v where v.room_id=r.id and v.turn_index=r.turn_index and public.party_slf_approved(r.id,r.turn_index,v.player_id,k.key,r.slf_letter,v.answers->>k.key))=1 then 20 when (select count(*) from public.party_slf_answers v where v.room_id=r.id and v.turn_index=r.turn_index and public.party_slf_approved(r.id,r.turn_index,v.player_id,k.key,r.slf_letter,v.answers->>k.key) and lower(trim(v.answers->>k.key))=lower(trim(a.answers->>k.key)))>1 then 5 else 10 end) from (select unnest(array['Stadt','Land','Fluss','Tier','Beruf']) key) k)) order by p.joined_at,p.id),'[]'::jsonb) into slf_results from public.party_members p left join public.party_slf_answers a on a.room_id=p.room_id and a.player_id=p.id and a.turn_index=r.turn_index where p.room_id=r.id and r.phase in ('slf_results','slf_review');
return jsonb_build_object('status',r.status,'phase',r.phase,'turn',r.turn_index,'roll',r.roll,'task',case when r.phase in ('event','finished') or m.id=active_player then r.task else null end,'players',arr,'code',r.code,'your_turn',m.id=active_player,'you_judge',(m.id=judge_player or (m.id=active_player and coalesce((select pm.is_bot from public.party_members pm where pm.id=judge_player),false))),'judge_is_bot',coalesce((select pm.is_bot from public.party_members pm where pm.id=judge_player),false),'judge_id',judge_player,'timer_started_at',r.timer_started_at,'server_now',clock_timestamp(),'slf_letter',r.slf_letter,'slf_deadline',r.slf_deadline,'slf_submitted',submitted,'slf_mine',mine,'slf_results',case when r.phase in ('slf_results','slf_review') then slf_results else null end,'slf_votes',case when r.phase='slf_review' then (select coalesce(jsonb_agg(jsonb_build_object('player_id',v.player_id,'category',v.category,'reviewer_id',v.reviewer_id,'approved',v.approved)),'[]'::jsonb) from public.party_slf_votes v where v.room_id=r.id and v.turn_index=r.turn_index) else '[]'::jsonb end,'your_id',m.id,'board_mode',r.board_mode,'laps',r.laps,'star_field',r.star_field,'star_price',150,'final_round',r.ending_at is not null,'roll_info',r.roll_info,'slf_winner',case when r.phase='slf_results' then (select coalesce(jsonb_agg(z.name),'[]'::jsonb) from jsonb_to_recordset(slf_results) as z(name text,round_points int) where z.round_points=(select max(t.round_points) from jsonb_to_recordset(slf_results) as t(name text,round_points int))) else null end);
end $function$;

create or replace function public.party_set_avatar(p_code text, p_token uuid, p_avatar text) returns jsonb
language plpgsql security definer set search_path='' as $f$
declare r public.party_rooms; m public.party_members;
begin
 select * into r from public.party_rooms where code=upper(trim(p_code));
 if not found then raise exception 'Lobby nicht gefunden'; end if;
 select * into m from public.party_members where room_id=r.id and token=p_token;
 if not found then raise exception 'Kein Zugang'; end if;
 if r.status='playing' then raise exception 'Figur nur in der Lobby änderbar'; end if;
 if p_avatar !~ '^A1(\.[0-9]{1,2}){9}$' then raise exception 'Ungültige Figur'; end if;
 update public.party_members set avatar=p_avatar where id=m.id;
 return public.party_snapshot(p_code,p_token);
end $f$;
