# CLI feature example

```text
Feature: operator can retry a failed job
Entry points: retry command, interactive action
States: failed, retrying, completed, cancelled
Terminals: completed, cancelled, error
Observables: exit status, visible job state, durable state after a new process reads it
Domain adapter supplies: command, fixture, process boundary, cleanup
```
