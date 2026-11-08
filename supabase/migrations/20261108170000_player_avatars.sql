-- Spielfiguren: Spalte hat speichert jetzt die gewählte Avatar-ID (100Avatars, 12 zur Wahl)
create or replace function public.party_hat_list()
returns text[] language sql immutable set search_path to '' as
$$ select array['002','027','038','052','046','079','086','088','087','120','160','093'] $$;

create or replace function public.party_member_default_hat()
returns trigger language plpgsql security definer set search_path to '' as $$
begin
  if new.hat is null or not (new.hat = any(public.party_hat_list())) then
    select h into new.hat from unnest(public.party_hat_list()) h
      where h not in (select coalesce(m.hat, '') from public.party_members m where m.room_id = new.room_id)
      order by random() limit 1;
    if new.hat is null then new.hat := (public.party_hat_list())[floor(random() * 12)::int + 1]; end if;
  end if;
  return new;
end $$;

update public.party_members set hat = (public.party_hat_list())[floor(random() * 12)::int + 1]
  where hat is null or not (hat = any(public.party_hat_list()));
