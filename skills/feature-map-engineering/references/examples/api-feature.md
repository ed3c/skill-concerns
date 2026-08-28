# API feature example

```text
Feature: client can rotate a credential
Entry point: supported API operation
States: active-old, rotating, active-new, rejected
Terminals: success, authorization error, validation error
Observables: response contract and externally usable new credential state
Domain adapter supplies: endpoint, authentication fixture, request driver, cleanup
```

An HTTP success alone is insufficient when the behavioral contract includes later credential use or revocation.
