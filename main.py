#!/usr/bin/env python3

import os
import sys
import time
import logging
from pathlib import Path
from hashlib import sha256
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag
from tqdm import tqdm
import psutil
from colorama import init, Fore, Style, Back
import getpass
import argparse
from datetime import datetime

# Initialisation
init(autoreset=True)
delay = 0.05  # Réduit pour une meilleure fluidité

# Configuration du logging avec un format plus propre
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

# Configuration du logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---- Fonctions d'interface améliorées ----
def print_banner():
    """Affiche une bannière d'accueil stylée"""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    🔐 CRYPTEUR SÉCURISÉ 🔐                   ║
║                                                              ║
║              Chiffrement AES-256-GCM Professionnel           ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_separator():
    """Affiche une ligne de séparation"""
    print(f"{Fore.BLUE}{'─' * 60}{Style.RESET_ALL}")

def typewriter_effect(text, delay=0.03, color=Fore.WHITE, end='\n'):
    """Effet machine à écrire amélioré avec gestion des couleurs"""
    for char in text:
        if char == '\n':
            sys.stdout.write('\n')
        else:
            sys.stdout.write(color + char + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(end)

def input_with_prompt(prompt, color=Fore.CYAN, secure=False):
    """Fonction d'input uniformisée avec style"""
    print(f"{color}{prompt}{Style.RESET_ALL}", end=" ")
    if secure:
        return getpass.getpass("")
    return input(f"{Fore.WHITE}>> {Style.RESET_ALL}")

def confirm_action(message, default=False):
    """Demande de confirmation avec gestion des valeurs par défaut"""
    default_text = "(O/n)" if default else "(o/N)"
    while True:
        response = input_with_prompt(f"{message} {default_text}").strip().lower()
        if not response:
            return default
        if response in ['o', 'oui', 'y', 'yes']:
            return True
        elif response in ['n', 'non', 'no']:
            return False
        typewriter_effect("⚠️ Veuillez répondre par 'o' (oui) ou 'n' (non)", color=Fore.YELLOW)

def display_menu():
    """Affiche le menu principal avec un style amélioré"""
    menu = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                         📋 MENU PRINCIPAL                    ║
╠══════════════════════════════════════════════════════════════╣
║  1. 🔐 Chiffrer un dossier                                   ║
║  2. 🔓 Déchiffrer un dossier                                 ║
║  3. 📊 Statistiques du dernier traitement                    ║
║  4. ⚙️  Paramètres                                            ║
║  5. ❓ Aide                                                  ║
║  6. ❌ Quitter                                               ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(menu)

def display_help():
    """Affiche l'aide avec des informations détaillées"""
    help_text = f"""
{Fore.GREEN}📖 AIDE - CRYPTEUR SÉCURISÉ{Style.RESET_ALL}

{Fore.YELLOW}🔐 CHIFFREMENT :{Style.RESET_ALL}
• Utilise l'algorithme AES-256 en mode GCM pour une sécurité maximale
• Chaque fichier est chiffré avec un vecteur d'initialisation unique
• Option d'ajout de l'extension '.encrypted' pour identifier les fichiers

{Fore.YELLOW}🔑 MOTS DE PASSE :{Style.RESET_ALL}
• Utilisez des mots de passe complexes (min. 12 caractères)
• Combinez majuscules, minuscules, chiffres et symboles
• Ne réutilisez jamais le même mot de passe

{Fore.YELLOW}💡 CONSEILS :{Style.RESET_ALL}
• Sauvegardez vos données avant chiffrement
• Testez le déchiffrement sur un petit dossier d'abord
• Conservez vos mots de passe en sécurité

{Fore.YELLOW}⚠️ ATTENTION :{Style.RESET_ALL}
• La perte du mot de passe rend les données irrécupérables
• Vérifiez l'espace disque disponible avant traitement
"""
    print(help_text)

def display_stats(stats):
    """Affiche les statistiques de traitement"""
    if not stats:
        typewriter_effect("📊 Aucune statistique disponible", color=Fore.YELLOW)
        return
    
    print(f"""
{Fore.GREEN}📊 STATISTIQUES DU DERNIER TRAITEMENT{Style.RESET_ALL}
{Fore.BLUE}{'─' * 50}{Style.RESET_ALL}
📁 Dossier traité : {stats.get('folder', 'N/A')}
🔢 Nombre de fichiers : {stats.get('files_count', 0)}
✅ Succès : {stats.get('success_count', 0)}
❌ Échecs : {stats.get('error_count', 0)}
📊 Taille totale : {format_size(stats.get('total_size', 0))}
⏱️ Durée : {stats.get('duration', 'N/A')}
🕐 Date : {stats.get('timestamp', 'N/A')}
""")

def format_size(size_bytes):
    """Formate la taille en unités lisibles"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def get_folder_stats(folder_path):
    """Calcule les statistiques d'un dossier"""
    total_size = 0
    file_count = 0
    
    try:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except (OSError, IOError):
                    continue
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques : {e}")
    
    return {'size': total_size, 'count': file_count}

def validate_folder_path(path):
    """Valide et normalise le chemin du dossier"""
    if not path:
        return None, "Chemin vide"
    
    path = Path(path).resolve()
    
    if not path.exists():
        return None, f"Le chemin '{path}' n'existe pas"
    
    if not path.is_dir():
        return None, f"'{path}' n'est pas un dossier"
    
    try:
        # Test d'accès en lecture
        list(path.iterdir())
    except PermissionError:
        return None, f"Accès refusé au dossier '{path}'"
    
    return str(path), None

def get_password_strength(password):
    """Évalue la force d'un mot de passe"""
    score = 0
    feedback = []
    
    if len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1
    else:
        feedback.append("Utilisez au moins 8 caractères")
    
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Ajoutez des minuscules")
    
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Ajoutez des majuscules")
    
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Ajoutez des chiffres")
    
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 2
    else:
        feedback.append("Ajoutez des caractères spéciaux")
    
    strength_levels = {
        (0, 2): ("Très faible", Fore.RED),
        (3, 4): ("Faible", Fore.YELLOW),
        (5, 6): ("Moyen", Fore.BLUE),
        (7, 8): ("Fort", Fore.GREEN)
    }
    
    for (min_score, max_score), (label, color) in strength_levels.items():
        if min_score <= score <= max_score:
            return score, label, color, feedback
    
    return score, "Très fort", Fore.GREEN + Style.BRIGHT, []

def setup_password():
    """Configuration du mot de passe avec évaluation de la force"""
    if not os.path.exists("password.hash"):
        typewriter_effect("🔐 Configuration du mot de passe d'accès", color=Fore.YELLOW)
        print_separator()
        
        while True:
            pw1 = input_with_prompt("Nouveau mot de passe :", secure=True).strip()
            
            if not pw1:
                typewriter_effect("🚫 Mot de passe vide non autorisé", color=Fore.RED)
                continue
            
            # Évaluation de la force
            score, strength, color, feedback = get_password_strength(pw1)
            print(f"Force du mot de passe : {color}{strength}{Style.RESET_ALL}")
            
            if feedback:
                print(f"{Fore.YELLOW}Suggestions :{Style.RESET_ALL}")
                for suggestion in feedback:
                    print(f"  • {suggestion}")
            
            if score < 5:
                if not confirm_action("Mot de passe faible. Continuer quand même ?"):
                    continue
            
            pw2 = input_with_prompt("Confirmez le mot de passe :", secure=True).strip()
            
            if pw1 != pw2:
                typewriter_effect("❌ Les mots de passe ne correspondent pas", color=Fore.RED)
                continue
            
            # Sauvegarde
            with open("password.hash", "w") as f:
                f.write(sha256(pw1.encode()).hexdigest())
            
            typewriter_effect("✅ Mot de passe configuré avec succès", color=Fore.GREEN)
            break

def load_password_hash():
    """Charge le hash du mot de passe"""
    try:
        with open("password.hash", "r") as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Erreur lors du chargement du mot de passe : {e}")
        sys.exit(1)

def authenticate(password_hash, max_attempts=3):
    """Authentification avec limitation des tentatives"""
    print_separator()
    typewriter_effect("🔐 Authentification requise", color=Fore.BLUE)
    
    for attempt in range(max_attempts):
        remaining = max_attempts - attempt
        prompt = f"Mot de passe ({remaining} tentative{'s' if remaining > 1 else ''} restante{'s' if remaining > 1 else ''}) :"
        
        password = input_with_prompt(prompt, secure=True).strip()
        
        if password.lower() == 'q':
            typewriter_effect("⚠️ Authentification annulée", color=Fore.YELLOW)
            return False
        
        if sha256(password.encode()).hexdigest() == password_hash:
            typewriter_effect("🔓 Accès autorisé", color=Fore.GREEN)
            return True
        else:
            if attempt < max_attempts - 1:
                typewriter_effect("❌ Mot de passe incorrect", color=Fore.RED)
            else:
                typewriter_effect("🚫 Trop de tentatives échouées. Accès refusé.", color=Fore.RED)
    
    return False

# ---- Fonctions de chiffrement/déchiffrement modifiées ----
def pad_key(key):
    return sha256(key).digest()[:32]

def is_encrypted_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            return f.read(9) == b"ENCRYPTED"
    except:
        return False

def encrypt_file(input_file, key, use_extension=True):
    from os import urandom
    header = b"ENCRYPTED"
    iv = urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    try:
        with open(input_file, 'rb') as f:
            plaintext = f.read()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        output_file = input_file + ".encrypted" if use_extension else input_file

        with open(output_file, 'wb') as f:
            f.write(header + encryptor.tag + iv + ciphertext)

        if use_extension:
            os.remove(input_file)

    except Exception as e:
        logger.error(f"❌ Erreur chiffrement {input_file} : {e}")
        raise

def decrypt_file(input_file, key, use_temp_name=False):
    if not is_encrypted_file(input_file):
        logger.info(f"🟡 Le fichier {input_file} n'est pas chiffré")
        return
    try:
        with open(input_file, 'rb') as f:
            header = f.read(9)
            tag = f.read(16)
            iv = f.read(16)
            ciphertext = f.read()
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        output_file = input_file.replace('.encrypted', '') if input_file.endswith('.encrypted') else input_file
        temp_file = output_file + "_temp_decrypt"

        if use_temp_name and not input_file.endswith('.encrypted'):
            with open(temp_file, 'wb') as f:
                f.write(plaintext)
            os.remove(input_file)
            os.rename(temp_file, input_file)
        else:
            with open(output_file, 'wb') as f:
                f.write(plaintext)
            os.remove(input_file)

    except InvalidTag:
        # Erreur spécifique pour mauvaise clé de déchiffrement
        raise ValueError("Clé de déchiffrement incorrecte")
    except Exception as e:
        logger.error(f"❌ Erreur déchiffrement {input_file}: {e}")
        raise

def test_decryption_key(files_to_process, key):
    """Test la clé de déchiffrement sur un fichier échantillon"""
    if not files_to_process:
        return True
    
    # Prendre le premier fichier pour tester
    test_file = files_to_process[0]
    try:
        # Test de déchiffrement sans sauvegarder
        with open(test_file, 'rb') as f:
            header = f.read(9)
            if header != b"ENCRYPTED":
                return True  # Pas un fichier chiffré
            
            tag = f.read(16)
            iv = f.read(16)
            ciphertext = f.read()
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        # On teste juste le déchiffrement sans sauvegarder
        decryptor.update(ciphertext) + decryptor.finalize()
        return True
        
    except InvalidTag:
        return False
    except Exception:
        return False

def process_folder(folder_path, key, operation='encrypt', use_extension=True):
    """Traite un dossier avec gestion des statistiques et validation de clé"""
    start_time = time.time()
    stats = {
        'folder': folder_path,
        'operation': operation,
        'files_count': 0,
        'success_count': 0,
        'error_count': 0,
        'total_size': 0,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Collecte des fichiers
    files_to_process = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            path = os.path.join(root, file)
            try:
                stats['total_size'] += os.path.getsize(path)
            except:
                pass
            
            if operation == 'encrypt':
                if use_extension:
                    if not file.endswith(".encrypted"):
                        files_to_process.append(path)
                else:
                    if not is_encrypted_file(path):
                        files_to_process.append(path)
            else:  # decrypt
                if is_encrypted_file(path):
                    files_to_process.append(path)
    
    stats['files_count'] = len(files_to_process)
    
    if not files_to_process:
        message = "📭 Aucun fichier à traiter trouvé"
        typewriter_effect(message, color=Fore.YELLOW)
        return stats
    
    # Test de la clé pour le déchiffrement
    if operation == 'decrypt':
        typewriter_effect("🔍 Validation de la clé de déchiffrement...", color=Fore.BLUE)
        if not test_decryption_key(files_to_process, key):
            typewriter_effect("❌ Clé de déchiffrement incorrecte !", color=Fore.RED)
            while True:
                retry = confirm_action("Voulez-vous réessayer avec une autre clé ?", default=True)
                if not retry:
                    typewriter_effect("⚠️ Déchiffrement annulé", color=Fore.YELLOW)
                    return stats
                
                new_key = input_with_prompt("🔑 Nouvelle clé de déchiffrement :", secure=True).strip()
                if not new_key:
                    typewriter_effect("🚫 Clé vide non autorisée", color=Fore.RED)
                    continue
                
                new_key_padded = pad_key(new_key.encode())
                if test_decryption_key(files_to_process, new_key_padded):
                    typewriter_effect("✅ Clé validée avec succès", color=Fore.GREEN)
                    key = new_key_padded
                    break
                else:
                    typewriter_effect("❌ Clé incorrecte, veuillez réessayer", color=Fore.RED)
    
    # Affichage des informations
    folder_stats = get_folder_stats(folder_path)
    print(f"""
{Fore.CYAN}📊 Informations du traitement :{Style.RESET_ALL}
📁 Dossier : {folder_path}
🔢 Fichiers à traiter : {stats['files_count']}
📊 Taille totale : {format_size(stats['total_size'])}
""")
    
    if not confirm_action(f"Continuer le {'chiffrement' if operation == 'encrypt' else 'déchiffrement'} ?", default=True):
        typewriter_effect("⚠️ Opération annulée", color=Fore.YELLOW)
        return stats
    
    # Traitement avec barre de progression
    operation_name = "🔐 Chiffrement" if operation == 'encrypt' else "🔓 Déchiffrement"
    with tqdm(total=len(files_to_process), desc=operation_name, 
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
        
        for file_path in files_to_process:
            try:
                if operation == 'encrypt':
                    encrypt_file(file_path, key, use_extension)
                else:
                    use_temp_name = not file_path.endswith('.encrypted')
                    decrypt_file(file_path, key, use_temp_name)
                stats['success_count'] += 1
            except Exception as e:
                logger.error(f"⚠️ Échec pour {file_path}: {e}")
                stats['error_count'] += 1
            pbar.update(1)
    
    # Calcul de la durée
    duration = time.time() - start_time
    stats['duration'] = f"{duration:.1f}s"
    
    # Affichage du résumé
    print(f"""
{Fore.GREEN}✅ Traitement terminé !{Style.RESET_ALL}
✅ Succès : {stats['success_count']}
❌ Échecs : {stats['error_count']}
⏱️ Durée : {stats['duration']}
""")
    
    return stats

def main():
    """Fonction principale avec interface améliorée"""
    print_banner()
    
    # Configuration et authentification
    setup_password()
    password_hash = load_password_hash()
    
    if not authenticate(password_hash):
        return
    
    # Variables de session
    last_stats = None
    
    # Boucle principale
    while True:
        print_separator()
        display_menu()
        choice = input_with_prompt("Votre choix :").strip()
        
        if choice == '1':  # Chiffrement
            print_separator()
            typewriter_effect("🔐 CHIFFREMENT DE DOSSIER", color=Fore.CYAN)
            
            folder_path = input_with_prompt("📁 Chemin du dossier à chiffrer :").strip().strip('"\'')
            folder_path, error = validate_folder_path(folder_path)
            
            if error:
                typewriter_effect(f"❌ {error}", color=Fore.RED)
                continue
            
            key = input_with_prompt("🔑 Clé de chiffrement :", secure=True).strip()
            if not key:
                typewriter_effect("🚫 Clé vide non autorisée", color=Fore.RED)
                continue
            
            use_extension = confirm_action("Ajouter l'extension '.encrypted' ?", default=True)
            
            try:
                last_stats = process_folder(folder_path, pad_key(key.encode()), 'encrypt', use_extension)
            except Exception as e:
                typewriter_effect(f"❌ Erreur : {e}", color=Fore.RED)
        
        elif choice == '2':  # Déchiffrement
            print_separator()
            typewriter_effect("🔓 DÉCHIFFREMENT DE DOSSIER", color=Fore.CYAN)
            
            folder_path = input_with_prompt("📁 Chemin du dossier à déchiffrer :").strip().strip('"\'')
            folder_path, error = validate_folder_path(folder_path)
            
            if error:
                typewriter_effect(f"❌ {error}", color=Fore.RED)
                continue
            
            key = input_with_prompt("🔑 Clé de déchiffrement :", secure=True).strip()
            if not key:
                typewriter_effect("🚫 Clé vide non autorisée", color=Fore.RED)
                continue
            
            try:
                last_stats = process_folder(folder_path, pad_key(key.encode()), 'decrypt')
            except Exception as e:
                typewriter_effect(f"❌ Erreur : {e}", color=Fore.RED)
        
        elif choice == '3':  # Statistiques
            print_separator()
            display_stats(last_stats)
        
        elif choice == '4':  # Paramètres
            print_separator()
            typewriter_effect("⚙️ PARAMÈTRES", color=Fore.CYAN)
            if confirm_action("Réinitialiser le mot de passe d'accès ?"):
                if os.path.exists("password.hash"):
                    os.remove("password.hash")
                setup_password()
                password_hash = load_password_hash()
                typewriter_effect("✅ Mot de passe réinitialisé", color=Fore.GREEN)
        
        elif choice == '5':  # Aide
            print_separator()
            display_help()
        
        elif choice == '6':  # Quitter
            typewriter_effect("👋 Au revoir !", color=Fore.YELLOW)
            break
        
        else:
            typewriter_effect("⚠️ Choix invalide", color=Fore.RED)
        
        # Pause avant de revenir au menu
        input(f"\n{Fore.BLUE}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Arrêt demandé par l'utilisateur{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"Erreur fatale : {e}")
        sys.exit(1)