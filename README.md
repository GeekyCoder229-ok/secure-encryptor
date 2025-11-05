# 🔐 Crypteur Sécurisé

Un outil de chiffrement/déchiffrement de dossiers professionnel utilisant l'algorithme **AES-256-GCM** avec une interface en ligne de commande intuitive et colorée.

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Encryption](https://img.shields.io/badge/encryption-AES--256--GCM-red)

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Sécurité](#-sécurité)
- [Structure du projet](#-structure-du-projet)
- [FAQ](#-faq)
- [Contribution](#-contribution)
- [Licence](#-licence)

## ✨ Fonctionnalités

### Principales

- 🔐 **Chiffrement AES-256-GCM** : Algorithme de chiffrement militaire
- 🔓 **Déchiffrement sécurisé** : Validation de la clé avant traitement
- 🎨 **Interface colorée** : Expérience utilisateur agréable avec effets visuels
- 📊 **Statistiques détaillées** : Suivi des opérations de chiffrement/déchiffrement
- 🔑 **Protection par mot de passe** : Authentification pour accéder au programme
- 📁 **Traitement récursif** : Chiffre tous les fichiers d'un dossier et sous-dossiers
- ⚡ **Barre de progression** : Suivi en temps réel du traitement

### Sécurité

- ✅ Vecteur d'initialisation (IV) unique pour chaque fichier
- ✅ Tag d'authentification GCM pour l'intégrité des données
- ✅ Validation de la force du mot de passe
- ✅ Limitation des tentatives d'authentification
- ✅ Test de la clé avant déchiffrement massif
- ✅ Gestion sécurisée des erreurs

## 🔧 Prérequis

- **Python 3.12** ou supérieur
- **Système d'exploitation** : Windows, Linux, macOS
- **Espace disque** : Suffisant pour doubler la taille des fichiers à chiffrer

## 📥 Installation

### 1. Cloner ou télécharger le projet

```bash
git clone https://github.com/votre-username/crypteur-securise.git
cd crypteur-securise
```

### 2. Créer un environnement virtuel

**Windows (PowerShell) :**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS :**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Fichier `requirements.txt`

```txt
cryptography>=41.0.0
tqdm>=4.66.0
colorama>=0.4.6
psutil>=5.9.0
```

## 🚀 Utilisation

### Lancement du programme

```bash
python crypteur.py
```

### Première utilisation

Au premier lancement, le programme vous demandera de configurer un **mot de passe d'accès** :

```
🔐 Configuration du mot de passe d'accès
Nouveau mot de passe : ********
Force du mot de passe : Fort
Confirmez le mot de passe : ********
✅ Mot de passe configuré avec succès
```

### Menu principal

```
╔══════════════════════════════════════════════════════════════╗
║                         📋 MENU PRINCIPAL                    ║
╠══════════════════════════════════════════════════════════════╣
║  1. 🔐 Chiffrer un dossier                                   ║
║  2. 🔓 Déchiffrer un dossier                                 ║
║  3. 📊 Statistiques du dernier traitement                    ║
║  4. ⚙️  Paramètres                                           ║
║  5. ❓ Aide                                                  ║
║  6. ❌ Quitter                                               ║
╚══════════════════════════════════════════════════════════════╝
```

### Chiffrer un dossier

1. Choisissez l'option **1** dans le menu
2. Entrez le chemin du dossier à chiffrer
3. Entrez une clé de chiffrement forte
4. Choisissez d'ajouter l'extension `.encrypted` (recommandé)
5. Confirmez le traitement

**Exemple :**
```
📁 Chemin du dossier à chiffrer : D:\Documents\Secret
🔑 Clé de chiffrement : ********
Ajouter l'extension '.encrypted' ? (O/n) >> o

📊 Informations du traitement :
📁 Dossier : D:\Documents\Secret
🔢 Fichiers à traiter : 42
📊 Taille totale : 125.3 MB

🔐 Chiffrement |████████████████████| 42/42 [00:12<00:00]

✅ Traitement terminé !
✅ Succès : 42
❌ Échecs : 0
⏱️ Durée : 12.3s
```

### Déchiffrer un dossier

1. Choisissez l'option **2** dans le menu
2. Entrez le chemin du dossier à déchiffrer
3. Entrez la clé de déchiffrement
4. Le programme teste d'abord la clé sur un fichier échantillon
5. Confirmez le traitement si la clé est valide

**En cas de mauvaise clé :**
```
🔍 Validation de la clé de déchiffrement...
❌ Clé de déchiffrement incorrecte !
Voulez-vous réessayer avec une autre clé ? (O/n) >> o
🔑 Nouvelle clé de déchiffrement : ********
✅ Clé validée avec succès
```

### Statistiques

L'option **3** affiche les statistiques du dernier traitement :

```
📊 STATISTIQUES DU DERNIER TRAITEMENT
──────────────────────────────────────────────────
📁 Dossier traité : D:\Documents\Secret
🔢 Nombre de fichiers : 42
✅ Succès : 42
❌ Échecs : 0
📊 Taille totale : 125.3 MB
⏱️ Durée : 12.3s
🕐 Date : 2025-11-05 14:32:15
```

### Paramètres

L'option **4** permet de réinitialiser le mot de passe d'accès au programme.

## 🔒 Sécurité

### Algorithme de chiffrement

- **AES-256** : Advanced Encryption Standard avec clé de 256 bits
- **Mode GCM** : Galois/Counter Mode pour l'authentification et le chiffrement
- **IV unique** : Chaque fichier utilise un vecteur d'initialisation différent
- **Tag d'authentification** : Vérifie l'intégrité des données

### Structure d'un fichier chiffré

```
[9 octets] Header : "ENCRYPTED"
[16 octets] Tag GCM : Authentification
[16 octets] IV : Vecteur d'initialisation
[Variable] Données chiffrées
```

### Bonnes pratiques

✅ **À FAIRE :**
- Utilisez des mots de passe complexes (min. 12 caractères)
- Combinez majuscules, minuscules, chiffres et symboles
- Sauvegardez vos données avant chiffrement
- Conservez vos clés en lieu sûr (gestionnaire de mots de passe)
- Testez le déchiffrement sur un petit dossier test

❌ **À NE PAS FAIRE :**
- Utiliser des mots de passe simples ou communs
- Réutiliser la même clé pour tous vos dossiers
- Oublier ou perdre votre clé de chiffrement
- Interrompre le programme pendant le traitement
- Modifier manuellement les fichiers chiffrés

### ⚠️ AVERTISSEMENT

> **La perte de la clé de chiffrement rend vos données définitivement irrécupérables.**
> 
> Il n'existe aucun moyen de récupérer des fichiers chiffrés sans la clé d'origine. Assurez-vous de conserver vos clés en sécurité !

## 📂 Structure du projet

```
crypteur-securise/
├── crypteur.py          # Programme principal
├── requirements.txt     # Dépendances Python
├── README.md           # Documentation
├── .gitignore          # Fichiers à ignorer par Git
├── password.hash       # Hash du mot de passe (généré automatiquement)
└── .venv/              # Environnement virtuel (non versionné)
```

## 💡 Exemples d'utilisation

### Chiffrer un dossier de documents sensibles

```bash
# Lancez le programme
python crypteur.py

# Dans le menu :
>> 1
📁 Chemin : D:\Documents\Confidential
🔑 Clé : MyS3cur3P@ssw0rd!2024
Ajouter l'extension '.encrypted' ? >> o
Continuer le chiffrement ? >> o
```

### Déchiffrer et restaurer les fichiers

```bash
# Lancez le programme
python crypteur.py

# Dans le menu :
>> 2
📁 Chemin : D:\Documents\Confidential
🔑 Clé : MyS3cur3P@ssw0rd!2024
Continuer le déchiffrement ? >> o
```

### Utilisation en ligne de commande (future fonctionnalité)

```bash
# Chiffrer
python crypteur.py --encrypt --folder "D:\Data" --key "MaClé123"

# Déchiffrer
python crypteur.py --decrypt --folder "D:\Data" --key "MaClé123"
```

## ❓ FAQ

### Comment choisir une bonne clé de chiffrement ?

Une bonne clé doit contenir :
- Au moins 12 caractères
- Majuscules et minuscules
- Chiffres
- Caractères spéciaux (!@#$%^&*)

**Exemple de clé forte :** `Cr7pt0!S3cur3#2024`

### Que se passe-t-il si j'oublie ma clé ?

**Vos données sont perdues définitivement.** AES-256 est un algorithme de chiffrement militaire incassable sans la clé. Il n'existe aucune backdoor ou méthode de récupération.

### Puis-je chiffrer des fichiers déjà chiffrés ?

Oui, mais ce n'est pas recommandé. Le programme détecte les fichiers déjà chiffrés et les ignore par défaut pour éviter le double chiffrement.

### Le programme fonctionne-t-il sur Linux/macOS ?

Oui, le programme est compatible avec tous les systèmes d'exploitation supportant Python 3.12+.

### Comment sauvegarder mes clés de chiffrement ?

Utilisez un **gestionnaire de mots de passe** (KeePass, Bitwarden, 1Password) ou notez-les dans un lieu physique sûr (coffre-fort).

### Quelle est la différence avec des outils comme 7-Zip ou VeraCrypt ?

- **7-Zip** : Compression + chiffrement d'archives
- **VeraCrypt** : Création de volumes chiffrés
- **Ce programme** : Chiffrement individuel de fichiers avec conservation de la structure des dossiers

### Le chiffrement ralentit-il mon ordinateur ?

Le chiffrement utilise le CPU mais reste raisonnable. Sur un ordinateur moderne, comptez environ 10-50 Mo/s selon votre matériel.

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Idées de contributions

- [ ] Mode ligne de commande avec arguments
- [ ] Support du chiffrement par glisser-déposer
- [ ] Interface graphique (GUI)
- [ ] Génération automatique de clés fortes
- [ ] Export des statistiques en CSV/JSON
- [ ] Mode de chiffrement sélectif (par extension)
- [ ] Compression avant chiffrement
- [ ] Support du chiffrement de fichiers individuels

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Remerciements

- [cryptography](https://cryptography.io/) - Bibliothèque de chiffrement
- [tqdm](https://tqdm.github.io/) - Barres de progression
- [colorama](https://pypi.org/project/colorama/) - Couleurs dans le terminal

## 📞 Support

Pour toute question ou problème :

- 🐛 Ouvrez une [issue](https://github.com/votre-username/crypteur-securise/issues)
- 💬 Discussions sur [GitHub Discussions](https://github.com/votre-username/crypteur-securise/discussions)
- 📧 Email : mpodereck@gmail.com

---

**⚠️ Disclaimer :** Cet outil est fourni "tel quel" sans garantie. Utilisez-le à vos propres risques. Les auteurs ne sont pas responsables de la perte de données résultant de l'utilisation de ce programme.