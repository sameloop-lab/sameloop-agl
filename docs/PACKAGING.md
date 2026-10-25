# Construction et livraison

## Paquets Python

Depuis le parent des projets, dans un environnement qui contient `build` :

```bash
python -m build sameloop-plant
python -m build sameloop-agl
```

Chaque projet produit un sdist `.tar.gz` et une wheel `.whl`. Le fichier wheel
AGL installe les configurations et scripts dans `share/sameloop-agl` sous le
préfixe d'installation. Le dépôt source conserve les tests et les documents.
Les dépendances tierces restent externes ; aucun binaire KUKSA n'est repackagé.

## RPM / OBS

Les recettes complètes sont dans `packaging/*.spec`. Les archives sources
créées par `python -m build` emploient des underscores dans leurs noms de
sdist ; les recettes utilisent ce nom. Elles requièrent les macros Python RPM
et les dépendances empaquetées, notamment `python3dist(kuksa-client)` et
`python3dist(sameloop-plant)` pour AGL. Les scripts ne lancent pas pip sur Internet
pendant le build RPM. **Recettes fournies mais non construites en mock/OBS.**

Construire d'abord sameloop-plant, puis disposer d'un paquet kuksa-client 0.6.0
et de ses dépendances dans les dépôts du builder. Cette disponibilité n'est pas
supposée dans Fedora/redpesk. Ne pas confondre wheel construite et RPM validé.

## Yocto / AGL

Aucune recette prétendument prête n'est fournie sans image AGL de référence.
La future couche devra fixer : version AGL/Yocto, version du broker, Python,
recettes gRPC/Protobuf, métadonnées VSS, unités systemd et règles de sécurité.
Les services doivent être lancés dans l'ordre broker → provider → controller ;
la reprise après panne du broker doit redémarrer les deux services en OFF.

Le suivi du dossier sameloop-dev-project précédent n'est pas modifié par ces
archives : importer ce rapport comme nouvelle preuve avant d'y mettre à jour
les composants. Ne pas faire passer l'image AGL, les UI connectées ou le matériel
à l'état validé sur la base de cette seule intégration Linux.
