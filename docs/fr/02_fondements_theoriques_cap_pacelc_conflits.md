# Fondements théoriques : CAP, PACELC et anatomie des conflits

> **Auteur** : Jean-Marie Renouard (`jmrenouard`) - [LightPath](https://www.lightpath.fr) | **Licence** : MIT

## 1. Classification CAP et PACELC des systèmes multi-maîtres

Le théorème **CAP** (Brewer) pose un choix en partition réseau (`P`). Le système privilégie la **cohérence forte** (`C`, *Linearizability*) ou la **disponibilité** en écriture (`A`). Le modèle **PACELC** (Abadi) complète cette analyse en ajoutant le comportement en régime normal (`E`, *Else*) : compromis entre **latence** (`L`) et **cohérence** (`C`).

| Famille architecturale | Sous partition (`P`) | Régime normal (`E`) | Classe PACELC | Solutions représentatives |
| :--- | :---: | :---: | :---: | :--- |
| **Logique asynchrone** | `A` (écritures locales continues) | `L` (commit local immédiat) | **PA/EL** | PG natif (`#1`), Spock (`#2`), pglogical (`#3`), Bucardo (`#9`) |
| **SQL distribué Raft/Paxos** | `C` (quorum strict exigé) | `C` (consensus avant ACK) | **PC/EC** | YugabyteDB (`#5`), CockroachDB (`#6`), Spanner (`#13`) |
| **Sharding MPP + 2PC** | `C` (shard/coordinateur indisponible) | `C` (validation synchrone 2PC) | **PC/EC** | Citus (`#7`), OpenTenBase (`#8`) |
| **Extension hybride (PGD)** | Configurable (`A` async / `C` Raft/CAMO) | Configurable (`L` ou `C`) | **PA/EL** ou **PC/EC** | EDB Postgres Distributed (`#4`) |
| **HA Mono-Primaire Synchrone** | `C` (arrêt primaire sans standby sync) | `C` (`remote_apply`) ou `L` (async) | **PC/EC** / **PC/EL** | Patroni + etcd (`#15`) |

Un système **PA/EL** (logique asynchrone) valide en sous-milliseconde sur le nœud local. Il diverge toutefois si deux clients modifient les mêmes lignes avant propagation du WAL. Un système **PC/EC** (Raft/Paxos) préserve l'invariant global, mais la minorité devient indisponible sans quorum ($\lfloor N/2 \rfloor + 1$).

---

## 2. Anatomie des 4 classes de conflits multi-maîtres

### 2.1 Conflit Write-Write et anomalie Lost Update

Deux nœuds $N_1$ et $N_2$ lisent la même ligne de solde $S_0 = 1000$ et exécutent simultanément une opération non commutative (`balance = balance + delta`) :
- Sur $N_1$ : `UPDATE accounts SET balance = balance + 100 WHERE id = 9001` $\rightarrow$ écrit `1100`.
- Sur $N_2$ : `UPDATE accounts SET balance = balance - 30 WHERE id = 9001` $\rightarrow$ écrit `970`.

Le WAL logique de PostgreSQL véhicule l'image **après modification** (*after-image*, `balance = 1100` ou `970`), jamais l'expression arithmétique `+100` ou `-30`. Sous une stratégie **LWW** (*Last-Write-Wins*), la transaction dont l'horodatage `commit_ts` est le plus récent écrase l'autre : l'état converge vers `1100` ou `970` au lieu du solde exact `1070`. C'est le **Lost Update** silencieux. Seules l'isolation stricte avec ré-essai (`SQLSTATE 40001` sous Raft) ou les colonnes **CRDT Delta-Apply** (stockant l'image *avant* et *après* pour appliquer le delta $\Delta = v_{\text{new}} - v_{\text{old}}$) préservent la somme exacte `1070`.

### 2.2 Conflit Insert-Insert (PK et index UNIQUE secondaires)

Deux nœuds génèrent chacun une clé `SERIAL` (`id = 1` sur $N_1$ et $N_2$). Ils peuvent aussi insérer le même `email` sous contrainte `UNIQUE(email)` :
- **Réplication native PG (`#1`)** : L'*apply worker* du nœud récepteur échoue avec `SQLSTATE 23505` (`duplicate key value violates unique constraint`) et **stoppe complètement la file de réplication** de la souscription concernée jusqu'à intervention manuelle (`ALTER SUBSCRIPTION ... SKIP` ou suppression locale).
- **LWW / Spock (`#2`)** : Un nœud applique ou conserve une seule ligne selon le `commit_timestamp` et consigne la ligne écartée dans une table d'exceptions.
- **Séquences distribuées** : L'évitement des collisions PK impose des séquences à pas décalés (`INCREMENT BY K START WITH node_id`) pour de petits clusters statiques, des UUIDv4/UUIDv7, ou des identifiants **Snowflake** 64 bits (horodatage + identifiant de nœud + compteur local).

### 2.3 Conflit Update-Delete et anomalie du Tombstone

$N_1$ met à jour une ligne $R$ (`UPDATE`) pendant que $N_2$ supprime cette même ligne (`DELETE`).
- Quand l'`UPDATE` de $N_1$ arrive sur $N_2$, la ligne $R$ n'existe plus : le moteur logique ignore la mise à jour (`row not found`) ou journalise un conflit `update_missing`.
- Quand le `DELETE` de $N_2$ arrive sur $N_1$, la ligne modifiée disparaît sur $N_1$ ou résiste selon la résolution sur `origin`/`commit_ts`. Sans marquage explicite de suppression (*tombstone* horodaté, difficile en PostgreSQL sans extension spécialisée), les deux nœuds risquent de diverger durablement.

### 2.4 Inversion de dépendance sur clés étrangères (FK)

Soit une table parente `orders` et une table enfant `order_items`. En maillage asynchrone à $N \ge 3$ nœuds, une commande créée sur $N_1$ et son article sur $N_2$ suivent des délais distincts vers $N_3$. L'`INSERT` enfant arrive parfois **avant** le parent et échoue en violation FK (`SQLSTATE 23503`). Un `DELETE` parent sur $N_1$ concurrent à un `INSERT` enfant sur $N_2$ provoque aussi `23503`, évitable par sérialisation ou *tenant affinity*.

---

## 3. Formalisation mathématique des limites physiques

### 3.1 Bornes RPO et RTO

Le **RPO** (*Recovery Point Objective*, fenêtre de perte de données maximale) et le **RTO** (*Recovery Time Objective*, durée d'indisponibilité) encadrent le choix entre asynchrone et consensus synchrone :

$$
\text{RPO}_{\text{sync}} = 0, \qquad \text{RPO}_{\text{async}} \ge \Delta t_{\text{WAL\_flush}} + \Delta t_{\text{net}} + \Delta t_{\text{apply}}
$$

Pour une architecture HA mono-primaire (Patroni), le basculement impose un délai d'élection et de routage :

$$
\text{RTO}_{\text{failover}} = T_{\text{detect}} + T_{\text{quorum\_promote}} + T_{\text{WAL\_replay}} + T_{\text{reroute}}
$$

À l'inverse, un cluster Raft reste ouvert en écriture. La perte d'un *leader* Raft gèle néanmoins ses plages pendant le *lease timeout* et la ré-élection ($T_{\text{election}}$).

### 3.2 Latence de commit sous consensus WAN

Dans un groupe Raft à $N$ réplicas sur WAN, chaque validation exige deux étapes. Elle demande le `fsync` sur le leader puis l'accord d'au moins $Q = \lfloor N/2 \rfloor + 1$ nœuds. Si $\text{RTT}_{\text{quorum}}$ désigne le temps d'aller-retour vers le $(Q-1)$-ième pair le plus proche et $L_{\text{disk}}$ la latence d'écriture `fsync` :

$$
L_{\text{commit\_Raft}} \approx 1 \cdot \text{RTT}_{\text{quorum}} + L_{\text{disk}} + L_{\text{txn\_coord}}
$$

Sous protocole **2PC** multi-shards couplé à Raft (YugabyteDB, CockroachDB, Citus 2PC), les phases *Prepare* et *Commit* s'additionnent. Chaque commit coûte au moins deux aller-retours réseau :

$$
L_{\text{commit\_2PC}} = 2 \cdot \text{RTT}_{\text{quorum}} + 2 \cdot L_{\text{disk}}
$$

Conséquence directe : entre Paris et Francfort ($\text{RTT} \approx 12\text{ ms}$), un commit 2PC synchrone coûte au minimum $24\text{ ms}$, plafonnant un fil d'exécution séquentiel à ~41 TPS. Entre l'Europe et la côte Est américaine ($\text{RTT} \approx 80\text{ ms}$), ce plafond chute sous les 7 à 12 TPS par session.

### 3.3 Fenêtre d'incertitude liée à la dérive d'horloge (HLC et LWW)

Les systèmes **LWW** (`track_commit_timestamp = on` dans PostgreSQL) dépendent de l'horloge système NTP des nœuds. Si l'erreur horloge maximale vaut $\epsilon_{\text{clock}}$, la fenêtre d'ambiguïté entre $N_1$ et $N_2$ est :

$$
\Delta t_{\text{skew}} = 2 \cdot \epsilon_{\text{clock}}
$$

Toute paire d'écritures concurrentes séparées de moins de $\Delta t_{\text{skew}}$ (souvent 5 à 50 ms sous NTP standard, voire plusieurs centaines de ms en machine virtuelle surchargée) peut voir son ordre causal **inversé** lors de la résolution LWW. Les horloges **HLC** (*Hybrid Logical Clocks*, YugabyteDB et CockroachDB) combinent temps physique et compteur de Lamport. Quand deux transactions tombent dans $\epsilon_{\text{clock}}$ (250–500 ms en NTP, $< 7\text{ ms}$ sous TrueTime), elles **redémarrent** (`SQLSTATE 40001`) pour éviter toute inversion causale.

### 3.4 Probabilité de collision d'identifiants non coordonnés

Si $k$ transactions insèrent ensemble des clés aléatoires dans un espace $N$, le paradoxe des anniversaires s'applique. La probabilité d'au moins une collision PK ou `UNIQUE` croît quadratiquement :

$$
P_{\text{collision}}(k, N) \approx 1 - \exp\left(-\frac{k^2}{2N}\right)
$$

Sur une clé 32 bits non coordonnée ($N = 2^{31}$) ou deux séquences à `1`, $P_{\text{collision}}$ atteint **100 % dès $k = 2$**. Même sur $10^6$ lignes chaudes, $k = 1\,500$ écritures simultanées donnent plus de $67\,\%$ de collision sur $\Delta t_{\text{lag}}$.
