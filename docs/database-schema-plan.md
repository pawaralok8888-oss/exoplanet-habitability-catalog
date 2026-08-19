# Database Schema Plan (Week 1, Module D)

This is a plain-English explanation of how our database will be structured.
This is the starting point for Week 2, where we'll write the actual SQL.

## Why we need 3 tables

Our app needs to store three kinds of things:
1. **Stars** — the host stars that planets orbit.
2. **Exoplanets** — the planets themselves, with their features and predicted score.
3. **Habitability Log** — a history of every prediction ever made for a planet, with a timestamp.

We keep these separate (instead of one giant table) because a star can have
multiple planets, and a planet can be re-scored multiple times over its
lifetime. Splitting them out avoids repeating data and lets us track
history properly.

---

## Table 1: `stars`

Stores basic info about each host star.

| Column | Type | Notes |
|---|---|---|
| star_id | INT, Primary Key | Unique ID for each star |
| star_name | VARCHAR | Name of the star |
| temperature | FLOAT | Surface temperature (used to calculate habitable zone) |
| luminosity | FLOAT | Brightness (used to calculate habitable zone) |
| distance_from_earth | FLOAT | In light-years |

**Primary Key:** `star_id` — uniquely identifies each star, no duplicates allowed.

---

## Table 2: `exoplanets`

Stores each planet and its calculated scores.

| Column | Type | Notes |
|---|---|---|
| planet_id | INT, Primary Key | Unique ID for each planet |
| planet_name | VARCHAR | Name of the planet |
| star_id | INT, Foreign Key → stars.star_id | Which star this planet orbits |
| discovery_year | INT | Year the planet was discovered |
| habitable_zone_flag | BOOLEAN | Is it inside its star's habitable zone? |
| esi_score | FLOAT | Earth Similarity Index score |
| predicted_habitability | FLOAT | Model's predicted probability of habitability |

**Primary Key:** `planet_id`
**Foreign Key:** `star_id` links to `stars.star_id`. This means every planet
*must* belong to a real star already in the `stars` table — the database
won't let us add a planet pointing to a star that doesn't exist. This keeps
our data consistent.

---

## Table 3: `habitability_log`

Keeps a history of predictions over time (instead of overwriting the score
each time, we log every change).

| Column | Type | Notes |
|---|---|---|
| log_id | INT, Primary Key | Unique ID for each log entry |
| planet_id | INT, Foreign Key → exoplanets.planet_id | Which planet this entry is about |
| predicted_score | FLOAT | The habitability score at that point in time |
| timestamp | DATETIME | When this prediction was logged |

**Primary Key:** `log_id`
**Foreign Key:** `planet_id` links to `exoplanets.planet_id`.

**How it fills automatically:** In Week 2, we'll write a MySQL **trigger**
that fires automatically whenever a row is inserted or updated in
`exoplanets`. The trigger will copy the new score into `habitability_log`
along with a timestamp — nobody has to do this by hand. This is also what
powers our "Confidence Drift" feature later (comparing a planet's newest
score to its previous one).

---

## Relationships, summarized

```
stars (1) ────< (many) exoplanets (1) ────< (many) habitability_log
```

- One star can have many planets.
- One planet can have many log entries (one per time it's scored).

---

## Open questions for the team to confirm before Week 2

- [ ] Are these exact column names/types okay with everyone?
- [ ] Any extra columns we're missing (e.g., planet radius, orbital period)?
- [ ] Confirmed: this matches the data contract from Day 0?

*Once the team agrees on this doc, we're ready to write the actual `CREATE TABLE` statements in Week 2.*