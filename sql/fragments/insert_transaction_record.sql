INSERT INTO public.uchibot_transactions (
    user_id, free_amount, paid_amount, transaction_type
)
VALUES (
    $1, $2, $3, $4
)
RETURNING id;
