UPDATE public.uchibot_users
SET
    user_name = $2
WHERE user_id = $1;