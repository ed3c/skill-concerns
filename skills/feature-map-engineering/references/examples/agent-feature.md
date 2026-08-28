# Agent/workflow feature example

```text
Feature: agent can resume a suspended run
Entry point: supported resume operation
States: suspended, resuming, running, completed, failed
Terminals: completed, failed, blocked external dependency
Observables: durable run state and required external side effect
Domain adapter supplies: run fixture, tool boundary, scheduler/runtime driver, receipt store
```

A model response claiming success is not the external side effect.
