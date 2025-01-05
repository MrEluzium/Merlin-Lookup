INSERT INTO public.uchibot_fragments (user_id, book_id, word_list, text_fragment)
VALUES ($1, $2, $3, $4)
ON CONFLICT (user_id, book_id, word_list) DO NOTHING;