# How-To: Run Topology Benchmarks

Use this procedure to execute benchmark suites and rebuild charts and offline dashboard bundles.

## Prerequisites

- Initialize the `env/multi-db-docker-env` submodule.
- Install Docker Engine, Docker Compose v2, `make`, and Python 3.
- Stop unrelated database containers that listen on lab ports.

> [!WARNING]
> Stop competing database stacks before a benchmark run, or port conflicts and shared host CPU skew corrupt latency results.

## Procedure

1. Initialize the submodule directory if it is absent:

```bash
make init-env
```

2. Validate all Bash scripts and Compose files:

```bash
make lint
```

3. Build the shared `pgbench` and `sysbench` container image:

```bash
make build-bench-image
```

4. If no active cluster stack runs, start the target suite or execute the full runner:

```bash
make bench-all
make bench-pg18
make bench-yt-cluster
make bench-optimized
```

5. Rebuild the 13 PNG charts and offline HTML explorer from `results/`:

```bash
make charts
make dashboard
```

> [!NOTE]
> Full multi-topology sweeps require more than one hour on a single host. Run a single suite if you have limited time.

## Validation

Run the test suite to verify CSV schema integrity, PNG headers, and dashboard bundles:

```bash
make test
```

## Rollback

Clean temporary build caches, generated site directories, and log files:

```bash
make clean
```

## Related Reference and Analysis

- Check metrics in [Reference Index](../03-reference/index.md).
- Read conflict analysis in [Explanation Index](../04-explanation/index.md).
