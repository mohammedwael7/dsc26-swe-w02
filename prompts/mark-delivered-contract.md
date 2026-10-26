Goal: Specify a contract-first FastAPI endpoint for a Tawseel courier to mark a parcel delivered. Do not write implementation code.

Context: Python 3.12, FastAPI. The existing API has `POST /v1/parcels/{parcel_id}/events` with `{"type":"deliver"}`; Parcel has `id`, `cod_amount_piastres`, and `state`.

Assumptions: trusted authentication middleware supplies `courier_id`; each parcel has `assigned_courier_id`; only `out_for_delivery` parcels can be delivered. Delivery proof is `recipient_name` plus `proof_photo_id`. For COD, `cod_collected_piastres` must exactly equal `cod_amount_piastres` (zero when COD is zero). State and proof are persisted together.

Specify request fields, auth rule, state rule, success response, and error responses. Unknown parcel=404; wrong courier=403; wrong state including repeated delivery=409; invalid/missing proof or COD amount=422. Every error is `application/problem+json` with type, title, status; errors never mutate the parcel. Success=200 and includes the parcel, delivered state, server timestamp, and proof fields. Tests: give at least four input-to-expected-status cases, including one edge case. Output exactly two sections: (1) Contract table, (2) Test cases. Call out assumptions that must be checked with the client.
