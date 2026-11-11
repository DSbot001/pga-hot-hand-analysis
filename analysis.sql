-- Derived views are rebuilt from the raw all_holes table.
DROP VIEW IF EXISTS analysis;
DROP VIEW IF EXISTS strokes_gained;
DROP VIEW IF EXISTS field_totals;
DROP VIEW IF EXISTS lagged_holes;
DROP VIEW IF EXISTS scored_holes;
DROP VIEW IF EXISTS round_courses;
DROP VIEW IF EXISTS complete_rounds;
DROP VIEW IF EXISTS clean;


-- Excluded events:
--   Zurich Classic: two-player team event, so scores are not individual.
--   Q-School: qualifying tournament, not a regular TOUR event.
--   Hero World Challenge: unofficial event with a small invitational field.
--   Barracuda Championship: played under modified Stableford. golfastr's
--     `score` column holds Stableford points, not strokes, so score - par
--     is meaningless (event average to_par of about -3.7, and 99% of holes
--     would count as birdie or better). 



CREATE VIEW clean AS
SELECT *
FROM all_holes
WHERE event_query NOT IN (
 'Zurich Classic of New Orleans',
 'PGA TOUR Q-School presented by Korn Ferry',
 'Hero World Challenge',
 'Barracuda Championship'
);


-- Keep rounds 1-4 with one valid score for each hole from 1 through 18.
CREATE VIEW complete_rounds AS
WITH valid_rounds AS (
    SELECT event_query, round, player_id
    FROM clean
    WHERE round BETWEEN 1 AND 4
    GROUP BY event_query, round, player_id
    HAVING COUNT(*) = 18
        AND COUNT(DISTINCT hole) = 18
        AND MIN(hole) = 1
        AND MAX(hole) = 18
        AND COUNT(score) = 18
        AND COUNT(par) = 18
)

SELECT h.*, 18 AS n_holes
FROM clean AS h
JOIN valid_rounds AS v
    ON h.event_query = v.event_query
    AND h.round = v.round
    AND h.player_id = v.player_id;



-- Par sequence is a course proxy, not a guaranteed unique course ID.
CREATE VIEW round_courses AS
SELECT DISTINCT event_query, round, player_id,
    GROUP_CONCAT(CAST(par AS INTEGER), '') OVER (
        PARTITION BY event_query, round, player_id
        ORDER BY hole
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS course_key
FROM complete_rounds;


CREATE VIEW scored_holes AS
SELECT h.*, c.course_key,
    h.score - h.par AS to_par,
    CASE
        WHEN h.hole <= 9 THEN 1
        ELSE 2
    END AS nine
FROM complete_rounds AS h
JOIN round_courses AS c
    ON h.event_query = c.event_query
    AND h.round = c.round
    AND h.player_id = c.player_id;





-- Preserve the original reset at holes 1 and 10.
CREATE VIEW lagged_holes AS
SELECT *, 
    LAG(to_par) OVER (
        PARTITION BY player_id, event_query, round, nine
        ORDER BY hole) AS prev_to_par
FROM scored_holes;


-- Field totals for each hole: how many players played the same event, round,
-- course proxy and hole, and their summed to_par.
CREATE VIEW field_totals AS
SELECT *,
    COUNT(*) OVER (PARTITION BY event_query, round, course_key, hole) AS n_field,
    SUM(to_par) OVER (PARTITION BY event_query, round, course_key, hole) AS field_sum
FROM lagged_holes;


-- Inner query:
--   hole_diff: the other players' average to_par on the same hole (the
--     current player is left out). Higher = harder hole.
-- Outer query:
--   sg: strokes gained on this hole = hole_diff - to_par. Positive = better
--     than the field.
--   prev_cat: previous-hole result in three groups ('birdie+', 'par',
--     'bogey+'); NULL on holes 1 and 10.
--   tot_sg / tot_n: the player's summed strokes gained and number of holes
--     over the whole season. event_sg / event_n: the same within the current
--     event.
CREATE VIEW strokes_gained AS
SELECT *,
    hole_diff - to_par AS sg,
    SUM(hole_diff - to_par) OVER (PARTITION BY player_id) AS tot_sg,
    COUNT(hole_diff) OVER (PARTITION BY player_id) AS tot_n,
    SUM(hole_diff - to_par) OVER (PARTITION BY player_id, event_query) AS event_sg,
    COUNT(hole_diff) OVER (PARTITION BY player_id, event_query) AS event_n
FROM (
    SELECT *,
        CASE WHEN prev_to_par IS NULL THEN NULL
            WHEN prev_to_par <= -1 THEN 'birdie+'
            WHEN prev_to_par = 0 THEN 'par'
            ELSE 'bogey+'
            END AS prev_cat,
        1.0 * (field_sum - to_par) / NULLIF(n_field - 1, 0) AS hole_diff
    FROM field_totals
);


-- player_skill: average strokes gained per hole in the player's OTHER events.
--   Leaving out the current event keeps the scores being modeled out of the
--   skill measure. NULL for players with only one event.
CREATE VIEW analysis AS
SELECT *,
    1.0 * (tot_sg - event_sg) / NULLIF(tot_n - event_n, 0) AS player_skill
FROM strokes_gained;
