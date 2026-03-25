# Provider Adapter Contract

The application is intentionally structured so data-source changes do not require broad application rewrites.

## Design rules

- Every provider category exposes a small shared interface.
- The rest of the application talks to the provider registry, not directly to specific vendors.
- New paid providers should usually require:
  - one new adapter file,
  - one registry entry,
  - and optional environment-variable configuration.

## Current provider categories

- `market`
- `fundamentals`
- `macro`
- `events`

## Replay requirement

Replay mode is a first-class feature.

Whenever the upstream source supports it, provider adapters should honor an `as_of` anchor so the app can:

- cut historical candles at a past time,
- build a forecast only from information available at that time,
- and compare that forecast with the realized path afterward.

If a provider cannot support true point-in-time behavior for a dataset, the adapter should document the limitation clearly.

## Expected adapter responsibilities

- normalize symbol handling if the vendor uses a custom format
- isolate authentication and rate-limit handling
- map provider-specific fields into app-level shapes
- keep provider-specific pagination and retries out of the service layer
- preserve a stable method signature for the rest of the application

## Planned future adapters

- `market/polygon.py`
- `market/databento.py`
- `fundamentals/intrinio.py`
- `fundamentals/fmp.py`
- `events/wall_street_horizon.py`
- `options/thetadata.py`

## Practical rule

If a future provider forces changes across the API routes, forecast service, and frontend at the same time, the provider abstraction has failed and should be tightened.