SELECT
    u.user_name,
    COUNT(DISTINCT f.id) AS fragment_count,
    COALESCE(SUM(t.paid_amount), 0) AS paid_tokens_spent,
    u.paid_tokens,
    u.free_tokens
FROM
    uchibot_users u
LEFT JOIN uchibot_fragments f
    ON u.user_id = f.user_id
    AND (f.created_at >= COALESCE($1, f.created_at))
    AND (f.created_at <= COALESCE($2, f.created_at))
LEFT JOIN uchibot_transactions t
    ON u.user_id = t.user_id
    AND t.transaction_type = 'remove'
    AND (t.timestamp >= COALESCE($1, t.timestamp))
    AND (t.timestamp <= COALESCE($2, t.timestamp))
GROUP BY
    u.user_id, u.user_name, u.paid_tokens, u.free_tokens
ORDER BY
    u.user_name;
