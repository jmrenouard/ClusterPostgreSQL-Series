# Guide : Exécuter les benchmarks des topologies

Exécutez cette procédure pour lancer les benchmarks et actualiser graphiques et explorateur.

## Prérequis

- Initialisez `env/multi-db-docker-env`.
- Installez Docker, Compose v2, `make` et Python 3.
- Arrêtez tout conteneur actif sur les ports du lab.

> [!WARNING]
> Arrêtez les autres bases avant le test, sinon les conflits de ports faussent la latence.

## Procédure

1. Initialisez le sous-module s'il est absent :

```bash
make init-env
```

2. Validez les scripts Bash et piles Compose :

```bash
make lint
```

3. Construisez l'image `pgbench` et `sysbench` :

```bash
make build-bench-image
```

4. Si aucun cluster ne tourne, lancez une suite cible ou complète :

```bash
make bench-all
make bench-pg18
make bench-yt-cluster
make bench-optimized
```

5. Générez les 13 graphiques PNG et l'explorateur HTML :

```bash
make charts
make dashboard
```

> [!NOTE]
> Une passe complète dure plus d'une heure. Lancez une seule suite si votre temps reste court.

## Validation

Exécutez les tests pour vérifier CSV, graphiques PNG et explorateur :

```bash
make test
```

## Retour arrière

Supprimez caches, journaux et dossiers générés :

```bash
make clean
```

## Référence et explications

- Métriques : [Index Référence](../03-reference/index.md).
- Analyse : [Index Explications](../04-explications/index.md).
