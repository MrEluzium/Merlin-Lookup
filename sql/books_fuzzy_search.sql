SELECT id, title, author, url, similarity(title || ' ' || author, $1) AS sim
FROM alter_bot_book
WHERE similarity(title || ' ' || author, $1) > 0.5
ORDER BY sim DESC
LIMIT 5;