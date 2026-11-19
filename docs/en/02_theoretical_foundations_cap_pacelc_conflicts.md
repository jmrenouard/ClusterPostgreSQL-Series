# 02 — Theoretical Foundations: CAP, PACELC, and Conflict Calculus

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

## 1. CAP and PACELC Classification

Eric Brewer's **CAP Theorem** states that during a network partition (`P`), a distributed data store must sacrifice either linearizable **Consistency (`C`)** or total **Availability (`A`)**. Because partitions are intermittent while wide-area network latency is permanent, Daniel Abadi's **PACELC Theorem** refines this trade-off: **if (`P`)**, choose **`A` or `C`**; **else (`E`)** during normal operation, choose **Latency (`L`) or Consistency (`C`)**.

PostgreSQL multi-master engines split sharply across the PACELC plane:

| Architecture Archetype | Representative Solutions | Partition (`P`) | Normal (`E`) | Guarantee |
| :--- | :--- | :---: | :---: | :--- |
| **Async Logical / Trigger Mesh** | PG Bidirectional (#1), pgEdge (#2), pglogical (#3), Bucardo (#9), SymmetricDS (#10) | **PA** (each partition accepts writes) | **EL** (local commit latency only) | Eventual convergence (`RPO > 0`); concurrent writes collide |
| **Distributed Consensus (Raft/Paxos)** | YugabyteDB (#5), CockroachDB (#6), EDB PGD CAMO/Eager (#4), Spanner (#13) | **PC** (minority side halts writes) | **EC** (quorum round-trip per commit) | Linearizable / Serializable (`RPO = 0`); bounded by WAN RTT |
| **Sharded Coordinator + 2PC** | Citus (#7), OpenTenBase (#8), Aurora Limitless (#12) | **PC** (affected shards stall on node loss) | **EC** (2PC for multi-shard / reference writes) | Shard-local ACID; distributed 2PC amplification |
| **Single-Primary Sync HA** | Patroni + `synchronous_commit = remote_apply` (#15) | **PC** (primary stalls or steps down without quorum) | **EC** (sync standby RTT per commit) | Zero conflicts, `RPO = 0`, single write bottleneck |
| **Single-Primary Async HA** | Patroni + `synchronous_commit = off/local` (#15) | **PA** (with fencing risk) / **PC** (with etcd quorum) | **EL** (local commit only) | Single writer, zero conflicts, bounded async lag (`RPO > 0`) |

No software layer escapes PACELC: an engine offering **sub-millisecond cross-region commits (`EL`)** cannot simultaneously guarantee **zero lost updates without conflict (`EC`)** across disconnected writers.

---

## 2. Anatomy of Multi-Master Conflicts

When two active writers (`Node A` and `Node B`) mutate overlapping data asynchronously before receiving each other's replication stream, four distinct classes of anomalies emerge:

### 2.1 Write-Write Lost Update (Non-Commutative Read-Modify-Write)

Consider an account initialized at `balance = 100`. Client 1 on `Node A` deposits `+50` (`UPDATE accounts SET balance = balance + 50`, writing `150` at $t_1$). Simultaneously, Client 2 on `Node B` withdraws `-20` (`UPDATE accounts SET balance = balance - 20`, writing `80` at $t_2 > t_1$).

Under **Last-Write-Wins (LWW)**, logical replication carries the full post-image row (`new_balance = 80`) or overwrites `150` with `80` because $t_2 > t_1$. The `+50` deposit silently vanishes (**Lost Update**). Resolving this requires either:
- **Conflict-Free Replicated Data Types (CRDTs) / Delta-Apply**: replicating the algebraic delta ($\Delta = +50$ and $\Delta = -20$) rather than the absolute post-image so $100 + 50 - 20 = 130$ converges identically on both nodes.
- **Pessimistic / Optimistic Consensus**: locking or aborting one transaction with `SQLSTATE 40001` so Client 2 retries after seeing `150`.

### 2.2 Insert-Insert Primary Key & Secondary `UNIQUE` Collisions

- **Surrogate Primary Key Collision**: Two nodes using independent `SERIAL` or `GENERATED ALWAYS AS IDENTITY` sequences (`1, 2, 3...`) simultaneously generate `id = 42` for two unrelated business entities. Even LWW destroys one customer record or halts the apply worker (`SQLSTATE 23505`).
- **Secondary `UNIQUE` Index Collision**: Even with globally unique PKs (UUIDv7, Snowflake), two users on `Node A` and `Node B` may register the same `email = 'alice@example.org'` concurrently. Because each node holds a distinct PK (`pk_A != pk_B`), **two conflicting rows now violate the `UNIQUE(email)` constraint**. Core PostgreSQL logical apply workers immediately crash-loop on `23505`; LWW policies must delete one entire valid user row to restore index integrity.

### 2.3 Update-Delete & Tombstone Races

`Node A` updates row `id = 7` (`status = 'SHIPPED'`) at $t_1$, while `Node B` issues `DELETE FROM orders WHERE id = 7` at $t_2$. When `Node A`'s `UPDATE` arrives at `Node B`, the target row no longer exists (`update_missing`). Conversely, if `Node B` deletes first and `Node A`'s update arrives without tombstone metadata, naive conflict handlers either ignore the update (silent divergence if order matters) or resurrect a deleted entity.

### 2.4 Foreign-Key Dependency Inversion

Parent `customer_id = 10` exists on both nodes. `Node A` executes `DELETE FROM customers WHERE id = 10` (locally valid because no child orders exist on `Node A` yet). Concurrently, `Node B` executes `INSERT INTO orders (id, customer_id) VALUES (900, 10)` (locally valid because customer `10` still exists on `Node B`). Replicating `DELETE` to `Node B` triggers a **Foreign Key violation (`23503`)**, whereas replicating `INSERT` to `Node A` also triggers **`23503`** — creating a **cyclic apply deadlock** across both replication streams.

---

## 3. Formal Quantitative Models

### 3.1 Recovery Point (`RPO`) and Recovery Time (`RTO`) Bounds

For an asynchronous logical or streaming topology with network replication lag $\Delta t_{\text{repl\_lag}}$ and apply queue depth $Q_{\text{apply}}$ processed at rate $\mu_{\text{apply}}$, data at risk upon sudden ungraceful node loss is bounded below by:

$$
\text{RPO}_{\text{async}} \ge \Delta t_{\text{repl\_lag}} + \frac{Q_{\text{apply}}}{\mu_{\text{apply}}}, \quad \text{RPO}_{\text{quorum}} = 0
$$

In quorum-replicated consensus (`RF >= 3`, majority $\lfloor N/2 \rfloor + 1$ committed before acknowledgment), committed transactions survive any $f < N/2$ simultaneous node failures with $\text{RPO}_{\text{quorum}} = 0$. Meanwhile, total recovery time (`RTO`) obeys:

$$
\text{RTO}_{\text{quorum}} = T_{\text{detect}} + T_{\text{election}} + T_{\text{recover}}
$$

where $T_{\text{detect}}$ is the missed-heartbeat lease timeout, $T_{\text{election}}$ is the Raft/Paxos leader re-election duration, and $T_{\text{recover}}$ is uncommitted intent cleanup and connection re-routing time.

### 3.2 Consensus Commit Latency Over WAN

In Raft or Multi-Paxos without fast-path colocation, a synchronous write transaction requires quorum log persistence plus coordinator round-trips (typically one round for intent write/lease validation and one round for commit consensus, or $2 \cdot \text{RTT}_{\text{quorum}}$ in distributed multi-tablet 2PC + Raft):

$$
L_{\text{commit}} = 2 \cdot \text{RTT}_{\text{quorum}} + L_{\text{disk}} + L_{\text{coord}}
$$

where $\text{RTT}_{\text{quorum}}$ is the round-trip time from the transaction coordinator to the nearest majority quorum of voters, $L_{\text{disk}}$ is local `fsync` latency, and $L_{\text{coord}}$ is CPU/serialization overhead. As an analytical illustration: across two regions separated by $\text{RTT}_{\text{quorum}} = 80\text{ ms}$ with $L_{\text{disk}} = 1\text{ ms}$ and $L_{\text{coord}} = 0.5\text{ ms}$, single-row commit latency cannot drop below $L_{\text{commit}} = 161.5\text{ ms}$ ($\approx 6.2\text{ sequential commits/s}$ per client thread) regardless of CPU count.

### 3.3 Clock-Skew Vulnerability Window in LWW & HLC

Timestamp-based LWW (`track_commit_timestamp` + NTP) relies on physical clocks synchronized within uncertainty $\varepsilon_{\text{NTP}}$. When two nodes compare commit timestamps across a network, the effective **causality ambiguity window** is:

$$
\Delta t_{\text{skew}} = |\text{clock}_A - \text{clock}_B| + 2\varepsilon_{\text{NTP}}
$$

If Client 1 updates row $r$ on `Node A`, observes the confirmation, and triggers Client 2 to overwrite row $r$ on `Node B` within $\Delta t < \Delta t_{\text{skew}}$, `Node B`'s physical clock can lag `Node A`'s timestamp. LWW then chooses Client 1's older write over Client 2's causally newer write, violating linearizability silently. Distributed SQL engines mitigate this via **Hybrid Logical Clocks (HLC)** (aborting or advancing timestamps when drift exceeds `--max_clock_skew`, e.g., $500\text{ ms}$) or Google's **TrueTime** commit-wait (`wait(2 * epsilon)` where $\varepsilon < 7\text{ ms}$).

### 3.4 Birthday-Paradox Collision Probability Under Async Multi-Master

Consider $k$ concurrent uncoordinated write batches per replication window $\Delta t_{\text{lag}}$ touching uniformly distributed keys across an effective active keyspace of size $N$. By the Birthday Paradox approximation, the probability of at least one same-key collision within a single async propagation window is:

$$
P_{\text{conflict}}(k, N) \approx 1 - \exp\!\left(-\frac{k^2}{2N}\right)
$$

Notice the quadratic scaling in $k$: for a hot account table with $N = 10{,}000$ active accounts and $k = 200$ concurrent writes inside a $100\text{ ms}$ WAN replication window, $k^2 / (2N) = 2.0$, yielding $P_{\text{conflict}} \approx 1 - e^{-2} \approx 86.5\%$. Skewed Zipfian access ($80\%$ of traffic hitting $1\%$ of rows) collapses the effective $N$ by two orders of magnitude, turning rare network hiccups into continuous conflict storms.

---

## 4. Isolation Levels vs Distributed Anomaly Matrix

| Isolation / Mode | Engines | Lost Update | Write Skew | Phantom Read | Cost / Failure Behavior |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Async LWW** | Native PG, pgEdge (non-CRDT), pglogical, Bucardo | **Occurs** | **Occurs** | **Occurs** | Zero commit blocking; silent overwrite on collision |
| **Async Delta-CRDT** | pgEdge Spock (`delta_apply`), EDB PGD CRDT | **Prevented** (for CRDT cols) | **Occurs** | **Occurs** | Commutative arithmetic converges; non-CRDT cols remain LWW |
| **Read Committed (Distributed)** | YugabyteDB (Wait-on-Conflict), Citus (single-shard) | **Prevented** (row lock) | **Occurs** | **Occurs** | Locks wait on remote tablet; lower retry rate than SSI |
| **Repeatable Read / Snapshot** | YugabyteDB (`RR`), PostgreSQL local | **Prevented** (`40001` abort) | **Occurs** | **Prevented** | First-committer wins; loser receives `SQLSTATE 40001` |
| **Serializable (SSI / HLC)** | CockroachDB (default), YugabyteDB (`SERIALIZABLE`), Spanner | **Prevented** | **Prevented** | **Prevented** | Highest correctness; requires client-side `40001` retry loops |
