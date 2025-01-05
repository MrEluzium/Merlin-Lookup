WITH updated AS (
    UPDATE public.uchibot_users
    SET free_tokens = free_tokens - $2
    WHERE user_id = $1
      AND free_tokens >= $2
    RETURNING free_tokens
)
SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM updated) THEN TRUE
        ELSE FALSE
    END AS success;