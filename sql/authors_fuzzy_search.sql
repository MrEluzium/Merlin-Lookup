SELECT author, similarity(author, $1) AS sim
FROM alter_bot_book
WHERE similarity(author, $1) > 0.3
ORDER BY sim DESC
LIMIT 5;