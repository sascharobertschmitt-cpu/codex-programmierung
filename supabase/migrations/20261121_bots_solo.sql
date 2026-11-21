-- Solo gegen Computer: groesseres Stadt-Land-Fluss-Lexikon, Bot-Tick (+10 Punkte, grosszuegigeres Abstimmen, Runde schliessen)
-- Bereits live eingespielt.
insert into public.party_slf_lexicon(category,term) values
('Stadt','augsburg'),
('Stadt','aachen'),
('Stadt','amsterdam'),
('Land','argentinien'),
('Land','australien'),
('Land','albanien'),
('Fluss','aare'),
('Fluss','alster'),
('Fluss','amazonas'),
('Tier','affe'),
('Tier','adler'),
('Tier','ameise'),
('Beruf','arzt'),
('Beruf','architekt'),
('Beruf','anwalt'),
('Stadt','berlin'),
('Stadt','bonn'),
('Stadt','bremen'),
('Land','belgien'),
('Land','brasilien'),
('Land','bolivien'),
('Fluss','bode'),
('Fluss','bille'),
('Fluss','brahmaputra'),
('Tier','bär'),
('Tier','biene'),
('Tier','büffel'),
('Beruf','bäcker'),
('Beruf','busfahrer'),
('Beruf','bauer'),
('Stadt','dresden'),
('Stadt','dortmund'),
('Stadt','düsseldorf'),
('Land','dänemark'),
('Land','deutschland'),
('Land','dschibuti'),
('Fluss','donau'),
('Fluss','drau'),
('Fluss','dnepr'),
('Tier','dachs'),
('Tier','delfin'),
('Tier','dackel'),
('Beruf','dachdecker'),
('Beruf','dirigent'),
('Beruf','detektiv'),
('Stadt','essen'),
('Stadt','erfurt'),
('Stadt','edinburgh'),
('Land','ecuador'),
('Land','england'),
('Land','estland'),
('Fluss','elbe'),
('Fluss','ems'),
('Fluss','eder'),
('Tier','esel'),
('Tier','elefant'),
('Tier','eule'),
('Beruf','elektriker'),
('Beruf','erzieher'),
('Beruf','eisverkäufer'),
('Stadt','frankfurt'),
('Stadt','freiburg'),
('Stadt','florenz'),
('Land','frankreich'),
('Land','finnland'),
('Land','fidschi'),
('Fluss','fulda'),
('Fluss','fils'),
('Fluss','fusch'),
('Tier','fuchs'),
('Tier','frosch'),
('Tier','flamingo'),
('Beruf','friseur'),
('Beruf','fotograf'),
('Beruf','florist'),
('Stadt','göttingen'),
('Stadt','genf'),
('Stadt','graz'),
('Land','griechenland'),
('Land','ghana'),
('Land','guatemala'),
('Fluss','garonne'),
('Fluss','ganges'),
('Fluss','glan'),
('Tier','giraffe'),
('Tier','gans'),
('Tier','gorilla'),
('Beruf','gärtner'),
('Beruf','goldschmied'),
('Beruf','geologe'),
('Stadt','hamburg'),
('Stadt','hannover'),
('Stadt','heidelberg'),
('Land','honduras'),
('Land','haiti'),
('Land','holland'),
('Fluss','havel'),
('Fluss','hase'),
('Fluss','hudson'),
('Tier','hase'),
('Tier','hund'),
('Tier','hamster'),
('Beruf','hausmeister'),
('Beruf','hebamme'),
('Beruf','heilpraktiker'),
('Stadt','köln'),
('Stadt','kiel'),
('Stadt','kassel'),
('Land','kanada'),
('Land','kenia'),
('Land','kroatien'),
('Fluss','kinzig'),
('Fluss','kocher'),
('Fluss','kongo'),
('Tier','katze'),
('Tier','kuh'),
('Tier','krokodil'),
('Beruf','koch'),
('Beruf','kellner'),
('Beruf','klempner'),
('Stadt','leipzig'),
('Stadt','lübeck'),
('Stadt','london'),
('Land','luxemburg'),
('Land','lettland'),
('Land','litauen'),
('Fluss','lahn'),
('Fluss','leine'),
('Fluss','loire'),
('Tier','löwe'),
('Tier','libelle'),
('Tier','luchs'),
('Beruf','lehrer'),
('Beruf','lokführer'),
('Beruf','landwirt'),
('Stadt','münchen'),
('Stadt','mainz'),
('Stadt','madrid'),
('Land','mexiko'),
('Land','marokko'),
('Land','malta'),
('Fluss','main'),
('Fluss','mosel'),
('Fluss','mulde'),
('Tier','maus'),
('Tier','marder'),
('Tier','möwe'),
('Beruf','maurer'),
('Beruf','metzger'),
('Beruf','maler'),
('Stadt','nürnberg'),
('Stadt','neapel'),
('Stadt','nizza'),
('Land','norwegen'),
('Land','nepal'),
('Land','niger'),
('Fluss','neckar'),
('Fluss','nil'),
('Fluss','nidda'),
('Tier','nashorn'),
('Tier','nilpferd'),
('Tier','nandu'),
('Beruf','notar'),
('Beruf','näherin'),
('Beruf','netzwerktechniker'),
('Stadt','paris'),
('Stadt','potsdam'),
('Stadt','passau'),
('Land','polen'),
('Land','portugal'),
('Land','peru'),
('Fluss','pegnitz'),
('Fluss','po'),
('Fluss','prüm'),
('Tier','pferd'),
('Tier','papagei'),
('Tier','pinguin'),
('Beruf','pilot'),
('Beruf','polizist'),
('Beruf','pfleger'),
('Stadt','rostock'),
('Stadt','rom'),
('Stadt','regensburg'),
('Land','russland'),
('Land','rumänien'),
('Land','ruanda'),
('Fluss','rhein'),
('Fluss','ruhr'),
('Fluss','rhône'),
('Tier','reh'),
('Tier','rabe'),
('Tier','robbe'),
('Beruf','richter'),
('Beruf','reporter'),
('Beruf','reiseleiter'),
('Stadt','stuttgart'),
('Stadt','salzburg'),
('Stadt','stockholm'),
('Land','spanien'),
('Land','schweden'),
('Land','schweiz'),
('Fluss','saale'),
('Fluss','spree'),
('Fluss','sieg'),
('Tier','schwein'),
('Tier','schlange'),
('Tier','spatz'),
('Beruf','schreiner'),
('Beruf','sänger'),
('Beruf','schauspieler'),
('Stadt','trier'),
('Stadt','tübingen'),
('Stadt','toulouse'),
('Land','türkei'),
('Land','thailand'),
('Land','tunesien'),
('Fluss','tauber'),
('Fluss','themse'),
('Fluss','tiber'),
('Tier','tiger'),
('Tier','taube'),
('Tier','tintenfisch'),
('Beruf','tischler'),
('Beruf','taxifahrer'),
('Beruf','tierarzt'),
('Stadt','wien'),
('Stadt','wuppertal'),
('Stadt','würzburg'),
('Land','wales'),
('Land','westsahara'),
('Fluss','weser'),
('Fluss','werra'),
('Fluss','wupper'),
('Tier','wolf'),
('Tier','wal'),
('Tier','wespe'),
('Beruf','winzer'),
('Beruf','wirt'),
('Beruf','wissenschaftler')
on conflict do nothing;

CREATE OR REPLACE FUNCTION public.party_bot_tick(p_code text, p_host_token uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare r public.party_rooms; n int; act public.party_members; judge public.party_members;
  b record; p record; ans jsonb; term text; cat text; did text := null; host_tok uuid;
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
    if r.board_mode = 'circuit' and not act.turbo and act.cash >= 250 and random() < 0.5 then
      perform public.party_action(p_code, act.token, null, 'buy_turbo');
    elsif r.board_mode = 'circuit' and act.vip = 0 and act.cash >= 300 and random() < 0.4 then
      perform public.party_action(p_code, act.token, null, 'buy_vip');
    end if;
    perform public.party_action(p_code, act.token, null, 'roll');
    did := 'roll';
  elsif r.phase = 'choice' and act.is_bot then
    perform public.party_action(p_code, act.token, null, case when r.roll_info ? 'star_offer' then (case when act.cash >= 150 then 'star_yes' else 'star_no' end) when act.cash >= 100 and random() < 0.65 then 'stairs_yes' else 'stairs_no' end);
    did := 'choice';
  elsif r.phase = 'event' and act.is_bot then
    perform public.party_action(p_code, act.token, null, 'event_next');
    did := 'event_next';
  elsif r.phase = 'task' and act.is_bot then
    if random() < 0.6 then
      update public.party_members set points = points + 10 where id = act.id;
      if r.board_mode = 'circuit' and r.roll_info->'card'->>'deck' = 'aufgabe' then
        update public.party_members set cash = cash + coalesce((r.roll_info->'card'->>'value')::int, 0) where id = act.id;
        update public.party_rooms set phase = 'event', timer_started_at = null,
          task = act.name || ' hat die Aufgabe gemeistert! +30 Münzen, +' || (r.roll_info->'card'->>'value') || ' Münzen' where id = r.id;
      else
        update public.party_rooms set phase = 'event', timer_started_at = null,
          task = act.name || ' hat die Aufgabe gemeistert! +10 Punkte' where id = r.id;
      end if;
    else
      update public.party_rooms set phase = 'event', timer_started_at = null,
        task = act.name || ' ist an der Aufgabe gescheitert.' where id = r.id;
    end if;
    did := 'task';
  elsif r.phase = 'slf' then
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
    if did is null and not exists (select 1 from public.party_members where room_id = r.id and not is_bot) then
      perform public.party_action(p_code, act.token, null, 'slf_stop');
      did := 'slf_stop';
    end if;
  elsif r.phase = 'slf_review' then
    for b in select * from public.party_members m where m.room_id = r.id and m.is_bot loop
      for p in select a.player_id, k.key cat, k.value val from public.party_slf_answers a
               cross join lateral jsonb_each_text(a.answers) k
               where a.room_id = r.id and a.turn_index = r.turn_index and a.player_id <> b.id
                 and trim(k.value) <> '' and upper(left(trim(k.value), 1)) = r.slf_letter
                 and not exists (select 1 from public.party_slf_votes v where v.room_id = r.id and v.turn_index = r.turn_index
                                 and v.player_id = a.player_id and v.category = k.key and v.reviewer_id = b.id) loop
        begin
          perform public.party_slf_vote(p_code, b.token, p.player_id, p.cat,
                                        public.party_slf_valid(p.cat, p.val, r.slf_letter) or random() < 0.85);
          did := 'slf_vote';
        exception when others then null;
        end;
      end loop;
    end loop;
    -- nothing left to vote on (e.g. nobody has a checkable word): close the round
    perform public.party_slf_finalize(r.id);
  elsif r.phase = 'slf_results' and act.is_bot then
    perform public.party_action(p_code, act.token, null, 'slf_next');
    did := 'slf_next';
  end if;

  return jsonb_build_object('did', did, 'snapshot', public.party_snapshot(p_code, host_tok));
end
$function$;
