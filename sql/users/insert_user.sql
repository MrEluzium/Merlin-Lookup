INSERT INTO public.uchibot_users (user_id, user_name)
VALUES ($1, $2)
ON CONFLICT (user_id) DO NOTHING;