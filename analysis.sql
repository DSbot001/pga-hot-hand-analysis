-- Derived views are rebuilt from the raw all_holes table.
DROP VIEW IF EXISTS analysis;
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
--     would count as birdie or better). Keeping it creates a large fake
--     post-birdie effect (-0.43 vs -0.04). Without it the raw gap is ~0.



CREATE VIEW clean AS
SELECT *
FROM all_holes
WHERE event_query NOT IN (
 'Zurich Classic of New Orleans',
 'PGA TOUR Q-School presented by Korn Ferry',
 'Hero World Challenge',
 'Barracuda Championship'
);


-- Preserve the original rule: 18 rows, round <= 4.
CREATE VIEW complete_rounds AS
SELECT *
FROM (
    SELECT *,
        COUNT(*) OVER (
            PARTITION BY event_query, round, player_id) AS n_holes
    FROM clean
    WHERE round <= 4
)
WHERE n_holes = 18;



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
        PARTITION BY player_id, tournament_id, round, nine 
        ORDER BY hole) AS prev_to_par 
FROM scored_holes;



CREATE VIEW analysis AS
SELECT *, 
CASE WHEN prev_to_par IS NULL THEN NULL
    WHEN prev_to_par <= -1 THEN 1 
    ELSE 0 
    END AS prev_birdie,
 1.0 * (field_sum - to_par) / NULLIF(n_field - 1, 0) AS hole_diff,
 1.0 * (tot_sum - event_sum) / NULLIF(tot_n - event_n, 0) AS player_skill
FROM (
 SELECT *,
    COUNT(*) OVER (PARTITION BY event_query, round, course_key, hole) AS n_field,
    SUM(to_par) OVER (PARTITION BY event_query, round, course_key, hole) AS field_sum,
    SUM(to_par) OVER (PARTITION BY player_id) AS tot_sum,
    COUNT(*) OVER (PARTITION BY player_id) AS tot_n,
    SUM(to_par) OVER (PARTITION BY player_id, event_query) AS event_sum,
    COUNT(*) OVER (PARTITION BY player_id, event_query) AS event_n
 FROM lagged_holes
);
