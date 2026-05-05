#!/usr/bin/env python3

import base64
import hmac
import json
import logging
import os
import sys
import time
from datetime import datetime
from hashlib import sha256
from pathlib import Path

import getpass
from colorama import Fore, Style, init
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from tqdm import tqdm


init(autoreset=True)

MAGIC = b"ENCRYPTED"
FORMAT_VERSION = b"\x01"
SALT_SIZE = 16
IV_SIZE = 12
TAG_SIZE = 16
CHUNK_SIZE = 1024 * 1024
PASSWORD_HASH_FILE = "password.hash"
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter("%(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def print_banner():
    banner = f"""
{Fore.CYAN}+------------------------------------------------------------+
|                    CRYPTEUR SECURISE                      |
|              Chiffrement AES-256-GCM + scrypt             |
+------------------------------------------------------------+{Style.RESET_ALL}
"""
    print(banner)


def print_separator():
    print(f"{Fore.BLUE}{'-' * 60}{Style.RESET_ALL}")


def typewriter_effect(text, delay=0.01, color=Fore.WHITE, end="\n"):
    for char in text:
        sys.stdout.write(color + char + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(end)


def input_with_prompt(prompt, color=Fore.CYAN, secure=False):
    print(f"{color}{prompt}{Style.RESET_ALL}", end=" ")
    if secure:
        return getpass.getpass("")
    return input(f"{Fore.WHITE}>> {Style.RESET_ALL}")


def confirm_action(message, default=False):
    default_text = "(O/n)" if default else "(o/N)"
    while True:
        response = input_with_prompt(f"{message} {default_text}").strip().lower()
        if not response:
            return default
        if response in ["o", "oui", "y", "yes"]:
            return True
        if response in ["n", "non", "no"]:
            return False
        typewriter_effect("Veuillez repondre par 'o' ou 'n'.", color=Fore.YELLOW)


def display_menu():
    menu = f"""
{Fore.CYAN}+------------------------------------------------------------+
|                         MENU PRINCIPAL                     |
+------------------------------------------------------------+
|  1. Chiffrer un dossier                                    |
|  2. Dechiffrer un dossier                                  |
|  3. Statistiques du dernier traitement                     |
|  4. Parametres                                             |
|  5. Aide                                                   |
|  6. Quitter                                                |
+------------------------------------------------------------+{Style.RESET_ALL}
"""
    print(menu)


def display_help():
    help_text = f"""
{Fore.GREEN}AIDE - CRYPTEUR SECURISE{Style.RESET_ALL}

{Fore.YELLOW}CHIFFREMENT :{Style.RESET_ALL}
- AES-256-GCM pour le chiffrement authentifie.
- Derivation de cle avec scrypt et sel unique par fichier.
- Lecture/ecriture par blocs pour gerer les gros fichiers.
- Ecriture dans un fichier temporaire avant remplacement.

{Fore.YELLOW}CONSEILS :{Style.RESET_ALL}
- Sauvegardez vos donnees avant un traitement massif.
- Utilisez une cle longue et unique.
- Testez le dechiffrement sur un petit dossier avant usage reel.

{Fore.YELLOW}ATTENTION :{Style.RESET_ALL}
- La perte de la cle rend les donnees irrecuperables.
"""
    print(help_text)


def display_stats(stats):
    if not stats:
        typewriter_effect("Aucune statistique disponible", color=Fore.YELLOW)
        return

    print(f"""
{Fore.GREEN}STATISTIQUES DU DERNIER TRAITEMENT{Style.RESET_ALL}
{Fore.BLUE}{'-' * 50}{Style.RESET_ALL}
Dossier traite : {stats.get('folder', 'N/A')}
Nombre de fichiers : {stats.get('files_count', 0)}
Succes : {stats.get('success_count', 0)}
Echecs : {stats.get('error_count', 0)}
Taille totale : {format_size(stats.get('total_size', 0))}
Duree : {stats.get('duration', 'N/A')}
Date : {stats.get('timestamp', 'N/A')}
""")


def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_folder_path(path):
    if not path:
        return None, "Chemin vide"

    path = Path(path).resolve()

    if not path.exists():
        return None, f"Le chemin '{path}' n'existe pas"
    if not path.is_dir():
        return None, f"'{path}' n'est pas un dossier"

    try:
        list(path.iterdir())
    except PermissionError:
        return None, f"Acces refuse au dossier '{path}'"

    return str(path), None


def get_password_strength(password):
    score = 0
    feedback = []

    if len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1
    else:
        feedback.append("Utilisez au moins 8 caracteres")

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
        feedback.append("Ajoutez des caracteres speciaux")

    strength_levels = {
        (0, 2): ("Tres faible", Fore.RED),
        (3, 4): ("Faible", Fore.YELLOW),
        (5, 6): ("Moyen", Fore.BLUE),
        (7, 8): ("Fort", Fore.GREEN),
    }

    for (min_score, max_score), (label, color) in strength_levels.items():
        if min_score <= score <= max_score:
            return score, label, color, feedback

    return score, "Tres fort", Fore.GREEN + Style.BRIGHT, []


def derive_key(password, salt):
    if isinstance(password, str):
        password = password.encode("utf-8")

    kdf = Scrypt(
        salt=salt,
        length=32,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        backend=default_backend(),
    )
    return kdf.derive(password)


def create_password_record(password):
    salt = os.urandom(SALT_SIZE)
    password_hash = derive_key(password, salt)
    return {
        "version": 1,
        "kdf": "scrypt",
        "n": SCRYPT_N,
        "r": SCRYPT_R,
        "p": SCRYPT_P,
        "salt": base64.b64encode(salt).decode("ascii"),
        "hash": base64.b64encode(password_hash).decode("ascii"),
    }


def save_password_record(record):
    with open(PASSWORD_HASH_FILE, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)


def verify_password_record(password, record):
    if isinstance(record, str):
        return hmac.compare_digest(sha256(password.encode()).hexdigest(), record)

    salt = base64.b64decode(record["salt"])
    expected_hash = base64.b64decode(record["hash"])
    actual_hash = derive_key(password, salt)
    return hmac.compare_digest(actual_hash, expected_hash)


def setup_password():
    if os.path.exists(PASSWORD_HASH_FILE):
        return

    typewriter_effect("Configuration du mot de passe d'acces", color=Fore.YELLOW)
    print_separator()

    while True:
        pw1 = input_with_prompt("Nouveau mot de passe :", secure=True).strip()

        if not pw1:
            typewriter_effect("Mot de passe vide non autorise", color=Fore.RED)
            continue

        score, strength, color, feedback = get_password_strength(pw1)
        print(f"Force du mot de passe : {color}{strength}{Style.RESET_ALL}")

        if feedback:
            print(f"{Fore.YELLOW}Suggestions :{Style.RESET_ALL}")
            for suggestion in feedback:
                print(f"  - {suggestion}")

        if score < 5 and not confirm_action("Mot de passe faible. Continuer quand meme ?"):
            continue

        pw2 = input_with_prompt("Confirmez le mot de passe :", secure=True).strip()
        if pw1 != pw2:
            typewriter_effect("Les mots de passe ne correspondent pas", color=Fore.RED)
            continue

        save_password_record(create_password_record(pw1))
        typewriter_effect("Mot de passe configure avec succes", color=Fore.GREEN)
        break


def load_password_hash():
    try:
        with open(PASSWORD_HASH_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    except Exception as e:
        logger.error(f"Erreur lors du chargement du mot de passe : {e}")
        sys.exit(1)


def authenticate(password_record, max_attempts=3):
    print_separator()
    typewriter_effect("Authentification requise", color=Fore.BLUE)

    for attempt in range(max_attempts):
        remaining = max_attempts - attempt
        prompt = f"Mot de passe ({remaining} tentative{'s' if remaining > 1 else ''} restante{'s' if remaining > 1 else ''}) :"
        password = input_with_prompt(prompt, secure=True).strip()

        if password.lower() == "q":
            typewriter_effect("Authentification annulee", color=Fore.YELLOW)
            return False

        if verify_password_record(password, password_record):
            if isinstance(password_record, str):
                save_password_record(create_password_record(password))
                typewriter_effect("Ancien hash migre vers scrypt", color=Fore.GREEN)
            typewriter_effect("Acces autorise", color=Fore.GREEN)
            return True

        if attempt < max_attempts - 1:
            typewriter_effect("Mot de passe incorrect", color=Fore.RED)
        else:
            typewriter_effect("Trop de tentatives echouees. Acces refuse.", color=Fore.RED)

    return False


def is_encrypted_file(file_path):
    try:
        with open(file_path, "rb") as f:
            return f.read(len(MAGIC)) == MAGIC
    except OSError:
        return False


def get_output_path(input_file, operation, use_extension=True):
    if operation == "encrypt":
        return input_file + ".encrypted" if use_extension else input_file
    if input_file.endswith(".encrypted"):
        return input_file[:-len(".encrypted")]
    return input_file


def get_temp_path(output_file):
    return output_file + ".tmp"


def encrypt_file(input_file, password, use_extension=True):
    salt = os.urandom(SALT_SIZE)
    iv = os.urandom(IV_SIZE)
    key = derive_key(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    output_file = get_output_path(input_file, "encrypt", use_extension)
    temp_file = get_temp_path(output_file)

    try:
        with open(input_file, "rb") as source, open(temp_file, "wb") as target:
            target.write(MAGIC + FORMAT_VERSION + salt + iv)
            while True:
                chunk = source.read(CHUNK_SIZE)
                if not chunk:
                    break
                target.write(encryptor.update(chunk))
            encryptor.finalize()
            target.write(encryptor.tag)

        os.replace(temp_file, output_file)
        if use_extension:
            os.remove(input_file)

    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        logger.error(f"Erreur chiffrement {input_file} : {e}")
        raise


def decrypt_file(input_file, password):
    if not is_encrypted_file(input_file):
        logger.info(f"Le fichier {input_file} n'est pas chiffre")
        return

    output_file = get_output_path(input_file, "decrypt")
    temp_file = get_temp_path(output_file)

    try:
        with open(input_file, "rb") as source:
            if source.read(len(MAGIC)) != MAGIC:
                return

            version = source.read(1)
            if version != FORMAT_VERSION:
                raise ValueError("Format chiffre non supporte par cette version")

            salt = source.read(SALT_SIZE)
            iv = source.read(IV_SIZE)
            file_size = os.path.getsize(input_file)
            ciphertext_start = len(MAGIC) + len(FORMAT_VERSION) + SALT_SIZE + IV_SIZE
            ciphertext_size = file_size - ciphertext_start - TAG_SIZE
            if ciphertext_size < 0:
                raise ValueError("Fichier chiffre invalide ou incomplet")

            source.seek(file_size - TAG_SIZE)
            tag = source.read(TAG_SIZE)
            source.seek(ciphertext_start)

            key = derive_key(password, salt)
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            remaining = ciphertext_size

            with open(temp_file, "wb") as target:
                while remaining > 0:
                    chunk = source.read(min(CHUNK_SIZE, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    target.write(decryptor.update(chunk))
                decryptor.finalize()

        os.replace(temp_file, output_file)
        if output_file != input_file:
            os.remove(input_file)

    except InvalidTag:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise ValueError("Cle de dechiffrement incorrecte")
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        logger.error(f"Erreur dechiffrement {input_file}: {e}")
        raise


def test_decryption_key(files_to_process, password):
    if not files_to_process:
        return True

    test_file = files_to_process[0]
    try:
        with open(test_file, "rb") as source:
            if source.read(len(MAGIC)) != MAGIC:
                return True

            version = source.read(1)
            if version != FORMAT_VERSION:
                return False

            salt = source.read(SALT_SIZE)
            iv = source.read(IV_SIZE)
            file_size = os.path.getsize(test_file)
            ciphertext_start = len(MAGIC) + len(FORMAT_VERSION) + SALT_SIZE + IV_SIZE
            ciphertext_size = file_size - ciphertext_start - TAG_SIZE
            if ciphertext_size < 0:
                return False

            source.seek(file_size - TAG_SIZE)
            tag = source.read(TAG_SIZE)
            source.seek(ciphertext_start)

            key = derive_key(password, salt)
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            remaining = ciphertext_size
            while remaining > 0:
                chunk = source.read(min(CHUNK_SIZE, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                decryptor.update(chunk)
            decryptor.finalize()
            return True

    except InvalidTag:
        return False
    except Exception:
        return False


def process_folder(folder_path, password, operation="encrypt", use_extension=True):
    start_time = time.time()
    stats = {
        "folder": folder_path,
        "operation": operation,
        "files_count": 0,
        "success_count": 0,
        "error_count": 0,
        "total_size": 0,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    files_to_process = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            path = os.path.join(root, file)
            try:
                stats["total_size"] += os.path.getsize(path)
            except OSError:
                pass

            if operation == "encrypt":
                if use_extension:
                    if not file.endswith(".encrypted"):
                        files_to_process.append(path)
                elif not is_encrypted_file(path):
                    files_to_process.append(path)
            elif is_encrypted_file(path):
                files_to_process.append(path)

    stats["files_count"] = len(files_to_process)

    if not files_to_process:
        typewriter_effect("Aucun fichier a traiter trouve", color=Fore.YELLOW)
        return stats

    if operation == "decrypt":
        typewriter_effect("Validation de la cle de dechiffrement...", color=Fore.BLUE)
        if not test_decryption_key(files_to_process, password):
            typewriter_effect("Cle de dechiffrement incorrecte !", color=Fore.RED)
            while True:
                retry = confirm_action("Voulez-vous reessayer avec une autre cle ?", default=True)
                if not retry:
                    typewriter_effect("Dechiffrement annule", color=Fore.YELLOW)
                    return stats

                password = input_with_prompt("Nouvelle cle de dechiffrement :", secure=True).strip()
                if not password:
                    typewriter_effect("Cle vide non autorisee", color=Fore.RED)
                    continue

                if test_decryption_key(files_to_process, password):
                    typewriter_effect("Cle validee avec succes", color=Fore.GREEN)
                    break

                typewriter_effect("Cle incorrecte, veuillez reessayer", color=Fore.RED)

    print(f"""
{Fore.CYAN}Informations du traitement :{Style.RESET_ALL}
Dossier : {folder_path}
Fichiers a traiter : {stats['files_count']}
Taille totale : {format_size(stats['total_size'])}
""")

    action = "chiffrement" if operation == "encrypt" else "dechiffrement"
    if not confirm_action(f"Continuer le {action} ?", default=True):
        typewriter_effect("Operation annulee", color=Fore.YELLOW)
        return stats

    operation_name = "Chiffrement" if operation == "encrypt" else "Dechiffrement"
    with tqdm(
        total=len(files_to_process),
        desc=operation_name,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
    ) as pbar:
        for file_path in files_to_process:
            try:
                if operation == "encrypt":
                    encrypt_file(file_path, password, use_extension)
                else:
                    decrypt_file(file_path, password)
                stats["success_count"] += 1
            except Exception as e:
                logger.error(f"Echec pour {file_path}: {e}")
                stats["error_count"] += 1
            pbar.update(1)

    duration = time.time() - start_time
    stats["duration"] = f"{duration:.1f}s"

    print(f"""
{Fore.GREEN}Traitement termine !{Style.RESET_ALL}
Succes : {stats['success_count']}
Echecs : {stats['error_count']}
Duree : {stats['duration']}
""")

    return stats


def main():
    print_banner()
    setup_password()
    password_hash = load_password_hash()

    if not authenticate(password_hash):
        return

    last_stats = None

    while True:
        print_separator()
        display_menu()
        choice = input_with_prompt("Votre choix :").strip()

        if choice == "1":
            print_separator()
            typewriter_effect("CHIFFREMENT DE DOSSIER", color=Fore.CYAN)

            folder_path = input_with_prompt("Chemin du dossier a chiffrer :").strip().strip('"\'')
            folder_path, error = validate_folder_path(folder_path)
            if error:
                typewriter_effect(error, color=Fore.RED)
                continue

            key = input_with_prompt("Cle de chiffrement :", secure=True).strip()
            if not key:
                typewriter_effect("Cle vide non autorisee", color=Fore.RED)
                continue

            use_extension = confirm_action("Ajouter l'extension '.encrypted' ?", default=True)

            try:
                last_stats = process_folder(folder_path, key, "encrypt", use_extension)
            except Exception as e:
                typewriter_effect(f"Erreur : {e}", color=Fore.RED)

        elif choice == "2":
            print_separator()
            typewriter_effect("DECHIFFREMENT DE DOSSIER", color=Fore.CYAN)

            folder_path = input_with_prompt("Chemin du dossier a dechiffrer :").strip().strip('"\'')
            folder_path, error = validate_folder_path(folder_path)
            if error:
                typewriter_effect(error, color=Fore.RED)
                continue

            key = input_with_prompt("Cle de dechiffrement :", secure=True).strip()
            if not key:
                typewriter_effect("Cle vide non autorisee", color=Fore.RED)
                continue

            try:
                last_stats = process_folder(folder_path, key, "decrypt")
            except Exception as e:
                typewriter_effect(f"Erreur : {e}", color=Fore.RED)

        elif choice == "3":
            print_separator()
            display_stats(last_stats)

        elif choice == "4":
            print_separator()
            typewriter_effect("PARAMETRES", color=Fore.CYAN)
            if confirm_action("Reinitialiser le mot de passe d'acces ?"):
                if os.path.exists(PASSWORD_HASH_FILE):
                    os.remove(PASSWORD_HASH_FILE)
                setup_password()
                password_hash = load_password_hash()
                typewriter_effect("Mot de passe reinitialise", color=Fore.GREEN)

        elif choice == "5":
            print_separator()
            display_help()

        elif choice == "6":
            typewriter_effect("Au revoir !", color=Fore.YELLOW)
            break

        else:
            typewriter_effect("Choix invalide", color=Fore.RED)

        input(f"\n{Fore.BLUE}Appuyez sur Entree pour continuer...{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Arret demande par l'utilisateur{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"Erreur fatale : {e}")
        sys.exit(1)
