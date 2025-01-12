-- Table: public.uchibot_fragments

-- DROP TABLE IF EXISTS public.uchibot_fragments;

CREATE TABLE IF NOT EXISTS public.uchibot_fragments
(
    id integer NOT NULL DEFAULT nextval('uchibot_fragments_id_seq'::regclass),
    user_id integer NOT NULL,
    book_id integer NOT NULL,
    word_list text[] COLLATE pg_catalog."default" NOT NULL,
    raw_text_fragment text COLLATE pg_catalog."default" NOT NULL,
    text_fragment text COLLATE pg_catalog."default" NOT NULL,
    search_type character varying(10) COLLATE pg_catalog."default" NOT NULL,
    transaction_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uchibot_fragments_pkey PRIMARY KEY (id),
    CONSTRAINT uchibot_fragments_book_id_fkey FOREIGN KEY (book_id)
        REFERENCES public.alter_bot_book (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT uchibot_fragments_transaction_id_fkey FOREIGN KEY (transaction_id)
        REFERENCES public.uchibot_transactions (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT uchibot_fragments_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.uchibot_users (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT uchibot_fragments_search_type_check CHECK (search_type::text = ANY (ARRAY['full'::character varying, 'book'::character varying]::text[]))
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.uchibot_fragments
    OWNER to postgres;