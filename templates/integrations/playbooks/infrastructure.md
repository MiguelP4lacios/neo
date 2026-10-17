# Playbook — Infrastructure, deploys and logs

What is actually running, versus what a manifest claims.

Standing facts about this workspace. Not dated events — see `agent-notes/YYYY/` for those. The bullets below are generic Kubernetes behaviour, pre-filled; append cluster access recipes, service quirks and log-backend traps as you learn them.

- "Merged" is not "deployed" — a GitOps rollout lags CI by minutes. Probe the route: a 401 on a new authenticated route means it exists and is guarded; a 404 means the pod still serves the old build. Compare against a sibling route to be sure the 404 is not the guard.
- When polling for a rollout, require the signal twice with a gap AND require a sibling route to agree — a rapid-fire loop can trip edge defences that answer with misleading status codes.
- Exact last-restart time: `kubectl get pod <name> -n <ns> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.finishedAt}'`.
- Deployment revision numbers are not chronological with ReplicaSet creation: an older ReplicaSet holding the highest revision is the signature of a rollback. List `kubectl get rs -l app=<name>` with revision and creationTimestamp columns to spot it.
- Events expire (about an hour by default): `Events: <none>` on `kubectl describe` does not mean nothing happened.
- Name-prefix siblings (`<svc>` vs `<svc>-worker`) are separate Deployments with separate config — check each one explicitly with an exact label selector.
- Feature flags often live in ConfigMaps, not in a Deployment's `env` block: `kubectl get cm -A -o json | jq -r '.items[] | .metadata.namespace as $ns | .metadata.name as $n | (.data // {}) | to_entries[] | select(.key | test("<FLAG>")) | "\($ns)/\($n)  \(.key)=\(.value)"'`.
- `kubectl logs --since=<N>h` is not a reliable N-hour window: log rotation can cap real history well below the request. Check the earliest returned timestamp; use the log backend for history.
- A backgrounded `kubectl port-forward` can die silently mid-session (later requests fail to connect). Check it is still running before blaming the query.
- A non-zero log-search hit count is not proof — read the matching lines before concluding (case-insensitive substrings match unrelated business data). When a search is empty, run a positive-control term you know exists to prove the search mechanism works.
