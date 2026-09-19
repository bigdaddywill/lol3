# Persistent Executor Ledger

Append-only operational history for the persistent worker.

## Entry format

- UTC timestamp
- task id
- worker id
- event
- checkpoint/result
- evidence or error

The ledger is operational history. It does not replace HOT_STATE or the durable fact/decision/failure ledgers.
