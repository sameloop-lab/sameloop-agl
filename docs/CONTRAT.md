# Contrat KUKSA 0.1.0

Le namespace `Vehicle.SameLoop` est privé à la démo, non normalisé par COVESA.
Le JSON chargé par le broker et le VSPEC correspondent au catalogue
`src/sameloop_agl/contract.py`. Le broker charge le JSON, pas le VSPEC.

| Signal | Type VSS | Producteur / usage |
|---|---|---|
| Settings | actuator string | target : requête `{id,mode,setpoint}` ; current : réglage accepté |
| Command | actuator string | target : contrôleur `{generation,sequence,demand}` ; current : retour du fournisseur |
| Faults | actuator string | target : laboratoire `{invalid,hot}` ; désactivé par défaut |
| Frame | sensor string | Échantillon cohérent du fournisseur, génération et séquence |
| State | sensor string | État cohérent du contrôleur, génération et séquence |
| Temperature | sensor double | °C ; dernière mesure, consulter la qualité |
| SensorValid | sensor boolean | Validité du capteur |
| FanApplied / FanRpm | sensor double | % appliqué / tours par minute |
| FanDemand | sensor double | % demandé par le contrôleur |
| Mode / Setpoint | sensor string / double | OFF ou AUTO / °C accepté |
| Available / Overheat | sensor boolean | Disponibilité / dernière alarme connue |
| Error | sensor string | Dernier refus de réglage, vide si aucun |

## Cohérence des données

Les champs séparés sont pratiques pour explorer KUKSA. Un client ne doit pas
supposer qu'un Get ou un Set multi-signaux offre une transaction métier globale.
Les enveloppes Frame, State et Settings portent donc chacune un objet cohérent
sur **un seul signal string**. C'est un choix de première version, avec un coût
JSON supplémentaire à annoncer lors des comparaisons ; pas du tout-Protobuf typé.

Le consommateur mémorise l'identité `(generation, sequence)` et l'heure monotone
locale de réception d'une nouvelle séquence. Relire une valeur en cache ne
rafraîchit pas sa qualité. Deux séquences croissantes de la même génération
sont nécessaires à l'acquisition/reprise. Une ancienne génération connue est
rejetée. Aucun timestamp monotone n'est comparé entre machines.

## Régulation

OFF : demande zéro. AUTO : `clamp(20 × (température - consigne), 0, 100)`.
Consigne finie 15..40 °C. Un réglage invalide est rejeté entièrement, sans changer
le mode ou la consigne. Température disponible : valide, finie -40..150 °C,
échantillon confirmé et reçu depuis moins de 1 seconde. Sinon demande zéro.
Alarme >50 °C même en OFF ; si la mesure disparaît, conserver l'alarme précédente
avec `alarm_quality: unavailable`. Une valeur indisponible n'est pas remplacée
par zéro. Le ventilateur conserve son inertie : demande zéro ≠ arrêt instantané.

Le fournisseur applique une commande seulement après validation des bornes et
de la séquence. Après 1 seconde sans **nouvelle** commande, la demande retombe
à zéro. L'intégration temporelle est coupée à l'échéance du watchdog. Au redémarrage
du fournisseur, la cible Command mise en cache est effacée. Le contrôleur
redémarre OFF/25. Une suspension de plus de 60 secondes arrête le fournisseur
avec erreur plutôt que d'inventer une trajectoire.

## Sécurité et limites

Le profil en clair est restreint au loopback dans notre client et nos scripts.
Il n'active pas JWT : **les catégories sensor/actuator ne sont pas des droits**.
Tout client local ayant accès au broker peut écrire des données, y compris les
signaux internes. Ce profil sert à une démonstration sur une machine de confiance.
Le verrou de processus est local à l'utilisateur, pas une exclusion distribuée.
TLS, mTLS, rôles, authentification, accès distant et commande de matériel sont
hors de cette livraison. La politique demande zéro en défaut est celle du
simulateur ; elle n'est pas une analyse de sûreté d'un refroidissement industriel.
