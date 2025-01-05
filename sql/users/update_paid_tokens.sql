UPDATE public.uchibot_users
SET
    paid_tokens = $2
WHERE user_id = $1;