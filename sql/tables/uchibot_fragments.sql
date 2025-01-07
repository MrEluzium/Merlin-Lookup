-- Table: public.uchibot_fragments

-- DROP TABLE IF EXISTS public.uchibot_fragments;

CREATE TABLE IF NOT EXISTS public.uchibot_fragments
(
    id integer NOT NULL DEFAULT nextval('uchibot_fragments_id_seq'::regclass),
    user_id integer,
    book_id integer NOT NULL,
    word_list text[] COLLATE pg_catalog."default" NOT NULL,
    text_fragment text COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT uchibot_fragments_pkey PRIMARY KEY (id),
    CONSTRAINT unique_user_book_words UNIQUE (user_id, book_id, word_list),
    CONSTRAINT uchibot_fragments_book_id_fkey FOREIGN KEY (book_id)
        REFERENCES public.alter_bot_book (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT uchibot_fragments_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.uchibot_users (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.uchibot_fragments
    OWNER to postgres;