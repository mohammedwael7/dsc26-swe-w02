## Status
Accepted

## Context
Dispatch, delivery, failure, retry and return rules will evolve as the client learns more. Keeping them inside HTTP handlers would make those rules hard to exercise independently and easy to duplicate.

## Decision
Represent lifecycle data with immutable domain values and implement transitions in the framework-free `app.domain.apply_event` function. The API translates its exception into an HTTP problem response.

## Consequences
The rules can be tested without starting a server, and the HTTP layer stays focused on transport concerns. A new lifecycle rule must be added to the domain function and reflected in its tests and API behavior.
