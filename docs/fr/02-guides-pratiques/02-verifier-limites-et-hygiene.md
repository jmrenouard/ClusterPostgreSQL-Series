# Guide : Vérifier limites, formules et hygiène

Exécutez ces vérifications avant chaque commit pour valider Compose, formules LaTeX, sécurité et builds EN/FR.

## Prérequis

- Installez Python 3 avec `PyYAML`, `mkdocs` et `mkdocs-material`.
- Vérifiez Node.js et `docker` pour la suite complète.

> [!CAUTION]
> Supprimez `site/` et `_site/` avant le commit, sinon les règles d'hygiène rejettent ces dossiers.

## Procédure

1. Vérifiez la syntaxe de chaque script shell et pile Compose :

```bash
make lint
```

2. Validez tests unitaires, formules LaTeX et sécurité :

```bash
make test
make check-math
make check-security
```

3. Générez et vérifiez le bundle GitHub Pages :

```bash
make pages-build
make pages-check
```

4. Construisez et vérifiez les portails MkDocs anglais et français :

```bash
make docs-build
make docs-check
```

5. Vérifiez que le diff reste sous 15 000 caractères :

```bash
git diff main...HEAD | wc -c
```

## Validation

Vérifiez que les tests, le bundle Pages et les deux builds `--strict` retournent `0`.

## Retour arrière

Effacez immédiatement les répertoires générés :

```bash
make clean
```

## Référence

Consultez les codes d'erreur dans l'[Index Référence](../03-reference/index.md).
