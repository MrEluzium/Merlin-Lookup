SELECT author, sim
FROM (
    SELECT author, similarity(author, $1) AS sim
    FROM alter_bot_book
    WHERE author % $1
       OR author ILIKE '%' || $1 || '%'
    ORDER BY similarity(author, $1) DESC
) subquery
GROUP BY author, sim
ORDER BY sim DESC
LIMIT 5;
