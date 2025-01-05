WITH updated AS (
    UPDATE public.uchibot_users
    SET paid_tokens = paid_tokens - $2
    WHERE user_id = $1
      AND paid_tokens >= $2
    RETURNING paid_tokens
)
SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM updated) THEN TRUE
        ELSE FALSE
    END AS success;