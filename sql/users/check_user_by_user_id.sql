SELECT EXISTS (SELECT 1 FROM public.uchibot_users WHERE user_id = $1);
