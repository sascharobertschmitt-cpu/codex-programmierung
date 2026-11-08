-- Rundkurs immer 3 Runden
do $do$
declare d text; n text;
begin
  d := pg_get_functiondef('public.party_action'::regproc);
  n := replace(d, $a$laps=case when p_action='start_circuit_3' then 3 else 2 end$a$, $b$laps=3$b$);
  if n = d then raise exception 'party_action unerwartet'; end if;
  execute n;
end
$do$;
