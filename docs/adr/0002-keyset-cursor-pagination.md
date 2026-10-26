## Status
Accepted

## Context
The parcel list is creation ordered and may be filtered by state. With offset pagination, changing the state of earlier parcels shifts later results and can make clients skip or repeat parcels.

## Decision
Issue opaque, app-local cursor tokens that point after the last returned creation sequence and are bound to the requested state filter. Reject tokens the app did not issue or tokens used with another filter.

## Consequences
Clients can continue through a state-filtered list after earlier parcels change state. The cursor is intentionally not a durable cross-process token; a future persistent service should encode and protect the same keyset position in a versioned token.
