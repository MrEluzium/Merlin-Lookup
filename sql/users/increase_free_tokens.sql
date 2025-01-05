UPDATE public.uchibot_users
SET free_tokens = free_tokens + $2
WHERE user_id = $1
RETURNING free_tokens;