SELECT book_id,
       SUM(frequency) AS total_frequency
FROM public.alter_bot_wordscount
WHERE word = ANY(ARRAY[$1::text[]])
GROUP BY book_id
ORDER BY total_frequency DESC
LIMIT $2;