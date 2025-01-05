UPDATE public.uchibot_users
SET
    total_paid_tokens_spent = $2
WHERE user_id = $1;