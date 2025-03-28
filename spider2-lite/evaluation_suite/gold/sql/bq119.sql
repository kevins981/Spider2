WITH hurricane_geometry AS (
  SELECT
    * EXCEPT (longitude, latitude),
    ST_GEOGPOINT(longitude, latitude) AS geom,
  FROM
    `bigquery-public-data.noaa_hurricanes.hurricanes`
  WHERE
    season = '2020'
    AND basin = 'NA'
    AND name != 'NOT NAMED'
),
dist_between_points AS (
  SELECT
    sid,
    name,
    season,
    iso_time,
    usa_wind,
    geom,
    ST_DISTANCE(geom, LAG(geom, 1) OVER (PARTITION BY sid ORDER BY iso_time ASC)) / 1000 AS dist
  FROM
    hurricane_geometry
),
total_distances AS (
  SELECT
    sid,
    name,
    season,
    iso_time,
    usa_wind,
    geom,
    SUM(dist) OVER (PARTITION BY sid ORDER BY iso_time ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_distance,
    SUM(dist) OVER (PARTITION BY sid) AS total_dist
  FROM
    dist_between_points
),
ranked_hurricanes AS (
  SELECT
    *,
    DENSE_RANK() OVER (ORDER BY total_dist DESC) AS dense_rank
  FROM
    total_distances
)

SELECT
  geom,cumulative_distance,usa_wind
FROM
  ranked_hurricanes
WHERE
  dense_rank = 3
ORDER BY
cumulative_distance;