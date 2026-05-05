# Crypteur Securise

Outil en ligne de commande pour chiffrer et dechiffrer recursivement les fichiers d'un dossier avec **AES-256-GCM**. Les cles issues des mots de passe sont derivees avec **scrypt** et chaque fichier possede son propre sel et son propre IV.

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Encryption](https://img.shields.io/badge/encryption-AES--256--GCM-red)

## Fonctionnalites

- Chiffrement/dechiffrement recursif de dossiers.
- AES-256-GCM avec verification d'integrite.
- Derivation de cle par `scrypt` avec sel unique par fichier.
- Ecriture par blocs pour eviter de charger les gros fichiers en memoire.
- Ecriture dans un fichier temporaire avant remplacement du fichier cible.
- Validation de la cle avant un dechiffrement massif.
- Authentification d'acces au programme avec hash scrypt sale.
- Barre de progression et statistiques du dernier traitement.

## Prerequis

- Python 3.12 ou superieur
- Windows, Linux ou macOS
- Espace disque suffisant pour creer les fichiers temporaires pendant le traitement

## Installation

```bash
git clone https://github.com/votre-username/secure-encryptor.git
cd secure-encryptor
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Utilisation

Lancer le programme:

```bash
python main.py
```

Au premier lancement, l'application demande un mot de passe d'acces. Ce mot de passe protege seulement l'ouverture du programme; il ne remplace pas la cle de chiffrement utilisee pour les fichiers.

Menu principal:

```text
1. Chiffrer un dossier
2. Dechiffrer un dossier
3. Statistiques du dernier traitement
4. Parametres
5. Aide
6. Quitter
```

## Securite

### Format d'un fichier chiffre

```text
[9 octets]  Header : ENCRYPTED
[1 octet]   Version du format
[16 octets] Sel scrypt
[12 octets] IV GCM
[Variable]  Donnees chiffrees
[16 octets] Tag GCM
```

### Choix techniques

- **AES-GCM** fournit a la fois confidentialite et authentification.
- **scrypt** ralentit les attaques par dictionnaire sur les mots de passe.
- **Sel unique par fichier**: deux fichiers chiffres avec le meme mot de passe n'ont pas la meme cle derivee.
- **IV unique par fichier**: indispensable avec GCM.
- **Fichier temporaire**: le programme ecrit d'abord dans `*.tmp`, puis remplace le fichier cible quand l'operation reussit.

### Bonnes pratiques

- Sauvegardez vos donnees avant de chiffrer un dossier important.
- Utilisez une cle longue, unique, stockee dans un gestionnaire de mots de passe.
- Testez le dechiffrement sur un petit dossier avant un usage reel.
- N'interrompez pas le programme pendant le traitement.

La perte de la cle de chiffrement rend les donnees irrecuperables.

## Structure du projet

```text
secure-encryptor/
├── main.py              # Programme principal
├── requirements.txt     # Dependances Python directes
├── README.md            # Documentation
├── LICENCE              # Licence MIT
└── password.hash        # Cree automatiquement au premier lancement
```

## Limites connues

- Le mode ligne de commande avec arguments n'est pas encore implemente.
- Les fichiers chiffres avec l'ancien format du projet ne sont pas dechiffres par le nouveau format.
- Le projet reste un outil personnel/educatif: testez toujours sur une copie de vos donnees.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENCE`.
