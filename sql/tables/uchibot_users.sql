-- Table: public.uchibot_users

-- DROP TABLE IF EXISTS public.uchibot_users;

CREATE TABLE IF NOT EXISTS public.uchibot_users
(
    id integer NOT NULL DEFAULT nextval('uchibot_users_id_seq'::regclass),
    user_id bigint NOT NULL,
    user_name text COLLATE pg_catalog."default" NOT NULL,
    registration_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    paid_tokens integer DEFAULT 0,
    free_tokens integer DEFAULT 3,
    total_paid_tokens_spent integer DEFAULT 0,
    CONSTRAINT uchibot_users_pkey PRIMARY KEY (id),
    CONSTRAINT uchibot_users_user_id_key UNIQUE (user_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.uchibot_users
    OWNER to postgres;
-- Index: idx_user_id

-- DROP INDEX IF EXISTS public.idx_user_id;

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_id
    ON public.uchibot_users USING btree
    (user_id ASC NULLS LAST)
    TABLESPACE pg_default;