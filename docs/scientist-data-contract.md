# Scientist workspace data contract

The scientist view is built from the PHL CSV and the existing database/API fields.
The headers below were checked against `data/processed/exoplanets_features.csv`.

| Scientist meaning | PHL CSV header | Database field |
| --- | --- | --- |
| Planet identity | `P_NAME` | `exoplanets.name` |
| Host identity | `S_NAME` | `stars.name` and `exoplanets.star_id` |
| Planet catalog ID | — | `exoplanets.planet_id` (database-generated) |
| Discovery | `P_YEAR`, `P_DETECTION` | `discovery_year`, `detection_method` |
| Mass, radius | `P_MASS`, `P_RADIUS` | `mass`, `radius` |
| Density, gravity, escape velocity | `P_DENSITY`, `P_GRAVITY`, `P_ESCAPE` | `density`, `gravity`, `escape_velocity` |
| Period, semi-major axis | `P_PERIOD`, `P_SEMI_MAJOR_AXIS` | `orbital_period`, `orbital_distance` |
| Temperature, planet type | `P_TEMP_EQUIL`, `P_TYPE` | `equilibrium_temp`, `planet_type` |
| Stellar flux | `P_FLUX` | `stellar_flux` |
| Conservative/optimistic HZ flags | `P_HABZONE_CON`, `P_HABZONE_OPT` | `habitable_zone_flag`, `habitable_zone_optimistic_flag` |
| ESI | `esi_score` (project-derived) | `esi_score` |
| Model estimate | — (computed by model pipeline) | `predicted_habitability` |
| Stellar type, temperature, mass, radius, age, luminosity | `S_TYPE`, `S_TEMPERATURE`, `S_MASS`, `S_RADIUS`, `S_AGE`, `S_LUMINOSITY` | matching `stars` fields |
| Conservative HZ distance boundaries | `S_HZ_CON_MIN`, `S_HZ_CON_MAX` | `hz_conservative_inner_au`, `hz_conservative_outer_au` |
| Source provenance | Project-defined | `data_source` |
| Assessment history | Not in the CSV | `habitability_log.predicted_habitability`, `prediction_timestamp` |

## Unit and meaning rules

- `P_HABZONE_CON` is used as the source conservative-zone flag. The project had
  compared `P_FLUX` directly to `S_HZ_CON_MIN/MAX`, which mixes Earth-relative
  flux with orbital distance in AU. `features.py` now uses the PHL flag instead.
- For the plot's flux band, convert the host's AU boundaries using
  `flux = stellar_luminosity / distance_AU²`; the inner distance yields the
  higher flux edge. Each host has its own range, so the chart asks for one host
  at a time.
- Missing values remain `NULL` and are counted as missing inputs. The saved
  model pipeline median-imputes its model features; the dashboard identifies
  which inputs are missing rather than presenting them as observed.
- The PHL CSV has 4,048 planet rows. `planet_id` is not a PHL header; the
  database creates it as a surrogate key. The preview uses PHL names as IDs.
- The preview CSV contains no time series. It therefore shows an empty-history
  message for drift. Connected databases can show their stored score history,
  but current history rows do not retain before/after physical-field values.

## Model limits shown in the workspace

On the current 80/20 stratified split, the test partition contained only 11
positive examples. Accuracy alone is not an adequate validation signal for
ranking candidates; evaluate recall, precision, calibration, and validation on
more independent positive examples before making scientific claims.
