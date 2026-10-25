# sameloop-agl — 0.1.0

**Bind & Seek — Same Control Loop, Different Embedded Stacks**

Première implémentation **KUKSA sur PC Linux**, en Python : un fournisseur
capteur/ventilateur et un contrôleur indépendants échangent via un vrai broker.
Ce projet prépare la variante AGL ; il ne livre pas une distribution AGL,
une image Yocto ni une nouvelle interface Flutter. Licence MIT.

Versions retenues : **KUKSA Databroker 0.7.1**, **kuksa-client 0.6.0**,
**API kuksa.val.v1** exclusivement. Le SDK fournit les modules Protobuf/gRPC ;
notre adaptateur appelle explicitement VAL v1 et ne bascule pas en v2.

## 1. Installer les deux projets

Extraire les deux dossiers `sameloop-plant` et `sameloop-agl` côte à côte.
Depuis leur répertoire parent sur Fedora :

```bash
sudo dnf install python3 python3-pip
python3 -m venv .venv
.venv/bin/python -m pip install -c sameloop-agl/constraints.txt ./sameloop-plant ./sameloop-agl
source .venv/bin/activate
```

Ne pas installer uniquement `sameloop-agl` en espérant trouver `sameloop-plant`
sur PyPI : les deux projets locaux doivent être fournis à pip. Aucun des deux
n'a été publié sur PyPI. Internet est nécessaire pour les dépendances.
`constraints.txt` fixe les dépendances utilisées lors des essais, sans hashes ;
ce n'est pas un dépôt de dépendances hors ligne. Python 3.12 a été testé.

## 2. Lancer le broker — terminal 1

Avec le binaire amont **0.7.1** déjà installé :

```bash
cd sameloop-agl
DATABROKER=/chemin/vers/databroker ./scripts/run-broker.sh
```

Le script charge `config/vss.json`, écoute uniquement `127.0.0.1:55555`, sans
TLS ni autorisation. Utiliser un broker dédié à cette démo, pas un broker partagé.
Les exécutables amont x86_64/aarch64 sont accessibles dans les
[releases officielles](https://github.com/eclipse-kuksa/kuksa-databroker/releases/tag/0.7.1).
Le binaire n'est pas inclus dans nos archives.

Alternative Fedora avec Podman :

```bash
sudo dnf install podman
cd sameloop-agl
./scripts/run-broker-podman.sh
```

Cette variante est fournie mais **non exécutée ici**. Elle publie le port sur
le loopback et utilise `:Z` pour le montage avec SELinux. Le tag 0.7.1 est fixé,
mais le digest d'image reste à figer pour une livraison industrielle.

## 3. Lancer les deux services — terminaux 2 et 3

Depuis le parent des deux projets, dans chaque terminal :

```bash
source .venv/bin/activate
sameloop-agl provider --allow-faults
```

Puis dans l'autre terminal :

```bash
source .venv/bin/activate
sameloop-agl controller
```

Le fournisseur simule température et ventilateur avec `sameloop-plant`.
Le contrôleur démarre **OFF, consigne 25 °C**. L'ordre provider/controller est
recommandé ; deux échantillons successifs sont nécessaires pour devenir disponible.
Les services tournent nominalement à 10 Hz, sans garantie temps réel dur.

## 4. Piloter — terminal 4

```bash
source .venv/bin/activate
sameloop-agl state
sameloop-agl set --mode AUTO --setpoint 25
sameloop-agl watch --count 10
sameloop-agl fault --invalid
sameloop-agl fault
sameloop-agl set --mode OFF --setpoint 25
```

`set` attend l'acquittement portant l'identifiant de sa requête, ou échoue après
3 secondes. `watch` utilise un abonnement gRPC réel ; Ctrl+C l'arrête.
`state` lit le dernier état en cache : il ne prouve pas à lui seul que le
contrôleur est encore vivant. Un futur écran doit vérifier progression des
séquences et réception récente. `fault` sans option rétablit le capteur normal ;
`fault --hot` augmente la chauffe. Sans `--allow-faults`, le provider ignore ces
injections. Aucun mode manuel de commande du ventilateur n'est exposé dans la CLI.

Arrêter les processus avec Ctrl+C. Sur erreur RPC, un service s'arrête avec
un code non nul et un message : pas de reconnexion silencieuse en 0.1.0.
Après un redémarrage du broker, relancer provider puis controller, puis demander
explicitement AUTO. Un verrou local évite deux services du même rôle pour le
même utilisateur/port ; il ne remplace pas les permissions du broker.

## Tests et packaging

```bash
python -m unittest discover -s sameloop-plant/tests -v
python -m unittest discover -s sameloop-agl/tests -v
python sameloop-agl/tests/integration.py --broker /chemin/vers/databroker
```

L'intégration utilise un port libre, lance ses propres processus puis les arrête.
Voir [les résultats et limites](docs/VALIDATION.md), [le contrat](docs/CONTRAT.md),
[le schéma](docs/ARCHITECTURE.md), [le packaging](docs/PACKAGING.md).
Les tests ne nécessitent pas Flutter, CAN ou une image AGL.
