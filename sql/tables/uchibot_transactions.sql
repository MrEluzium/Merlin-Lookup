-- Table: public.uchibot_transactions

-- DROP TABLE IF EXISTS public.uchibot_transactions;

CREATE TABLE IF NOT EXISTS public.uchibot_transactions
(
    id integer NOT NULL DEFAULT nextval('uchibot_transactions_id_seq'::regclass),
    user_id bigint NOT NULL,
    free_amount integer NOT NULL,
    paid_amount integer NOT NULL,
    transaction_type character varying(10) COLLATE pg_catalog."default" NOT NULL,
    "timestamp" timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uchibot_transactions_pkey PRIMARY KEY (id),
    CONSTRAINT fk_uchibot_users FOREIGN KEY (user_id)
        REFERENCES public.uchibot_users (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT uchibot_transactions_free_amount_check CHECK (free_amount >= 0),
    CONSTRAINT uchibot_transactions_paid_amount_check CHECK (paid_amount >= 0),
    CONSTRAINT uchibot_transactions_transaction_type_check CHECK (transaction_type::text = ANY (ARRAY['add'::character varying, 'remove'::character varying]::text[]))
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.uchibot_transactions
    OWNER to postgres;
-- Index: idx_transactions_user_id

-- DROP INDEX IF EXISTS public.idx_transactions_user_id;

CREATE INDEX IF NOT EXISTS idx_transactions_user_id
    ON public.uchibot_transactions USING btree
    (user_id ASC NULLS LAST)
    TABLESPACE pg_default;