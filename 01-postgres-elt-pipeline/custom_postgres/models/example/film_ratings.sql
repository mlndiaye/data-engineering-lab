-- depends_on: {{ ref('films') }}
-- depends_on: {{ ref('film_actors') }}
-- depends_on: {{ ref('actors') }}
{{ generate_film_ratings() }}