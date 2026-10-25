# Validation — 25 octobre 2026

Version 0.1.0. Essais exécutés dans un environnement Linux x86_64 isolé,
Python 3.12.14, KUKSA Databroker 0.7.1 officiel, kuksa-client 0.6.0,
grpcio 1.84.1, protobuf 7.36.2. Versions Python complémentaires dans constraints.txt.

- 8 tests unitaires réussis : démarrage, cache et fraîcheur, modes et bornes,
  rejet atomique, qualité d'alarme, génération et ordre, métadonnées.
- 13 scénarios avec broker réel et deux services en processus séparés réussis.
- Un abonnement gRPC réel testé, en plus des Get/Set des services.
- Construction wheel/sdist Python effectuée.

Journaux : `unit-results.txt`, `integration-results.txt`. La suite d'intégration
lance un broker sur un port libre et arrête tous les processus qu'elle crée.

```bash
python -m unittest discover -s tests -v
python tests/integration.py --broker /chemin/vers/databroker
```

Binaire officiel essayé : `databroker-amd64-0.7.1.tar.gz`.
SHA256 de son archive :
`bfad889720a21e2823542e66a3bfab7140dcadcf8a760600507c3e762ca68b92`.
Révision annoncée : `a79e2420b319cedccd98298e2a75ee78cfca4b87`.
Ce hash décrit l'archive effectivement téléchargée, pas une signature tierce.

## Portée exacte

Les résultats prouvent la boucle KUKSA Linux et les scénarios listés dans le
journal. Ils ne prouvent pas une image AGL complète ni une UI connectée.
Non exécutés : Podman, RPM/mock/OBS, recette Yocto, aarch64, Fedora utilisateur,
TLS/mTLS/JWT, CAN, Zephyr et matériel. Aucun benchmark de latence n'est annoncé.
Le broker n'est pas inclus dans les archives SameLoop.
