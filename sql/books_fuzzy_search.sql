SELECT id, title, author, url, similarity(title || ' ' || author, %s) AS sim
FROM alter_bot_book
WHERE similarity(title || ' ' || author, %s) > 0.3
ORDER BY sim DESC
LIMIT 5;