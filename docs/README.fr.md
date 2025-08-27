# MTGA

<picture>
    <img alt="MTGA" src="https://github.com/BiFangKNT/mtga/blob/gui/icons/hero-img_f0bb32.png?raw=true">
</picture>

[![English](https://img.shields.io/badge/docs-English-purple)](README.en.md) [![简体中文](https://img.shields.io/badge/文档-简体中文-yellow)](../README.md) [![日本語](https://img.shields.io/badge/ドキュ-日本語-b7003a)](README.ja.md) [![한국어 문서](https://img.shields.io/badge/docs-한국어-green)](README.ko.md) [![Documentación en Español](https://img.shields.io/badge/docs-Español-orange)](README.es.md) [![Documentation en Français](https://img.shields.io/badge/docs-Français-blue)](README.fr.md) [![Documentação em Português (Brasil)](<https://img.shields.io/badge/docs-Português-purple>)](README.pt.md) [![Dokumentation auf Deutsch](https://img.shields.io/badge/docs-Deutsch-darkgreen)](README.de.md) [![Документация на русском языке](https://img.shields.io/badge/доки-Русский-darkblue)](README.ru.md)

## Introduction

MTGA est une solution basée sur un proxy local pour fournisseurs de modèles fixes d'IDE, compatible avec Windows et macOS.

**Note : Ce projet ne prend actuellement en charge que les API au format openai, veuillez le confirmer. Les autres formats peuvent être convertis au format openai avant utilisation.**

<details>
  <summary>Tu ne vois rien~~</summary>
  <br>
  <p>MTGA signifie Make T Great Again !</p>
 </details>

## Table des matières

* [Journal des modifications](#journal-des-modifications)
* [Démarrage rapide](#démarrage-rapide)
  * [Utilisateurs Windows (méthode de démarrage en un clic avec GUI)](#utilisateurs-windows-méthode-de-démarrage-en-un-clic-avec-gui)
  * [Utilisateurs macOS (installation d'application)](#utilisateurs-macos-installation-dapplication)
* [Démarrage à partir d'un script](#démarrage-à-partir-dun-script)
  * [Étape 0 : Préparation de l'environnement](#étape-0--préparation-de-lenvironnement)
    * [Windows](#windows)
      * [Étape 1 : Générer un certificat auto-signé](#étape-1--générer-un-certificat-auto-signé)
      * [Étape 2 : Faire confiance à votre certificat d'autorité de certification par Windows](#étape-2--faire-confiance-à-votre-certificat-dautorité-de-certification-par-windows)
      * [Étape 3 : Modifier le fichier Hosts](#étape-3--modifier-le-fichier-hosts)
      * [Étape 4 : Exécuter le serveur proxy local (Python)](#étape-4--exécuter-le-serveur-proxy-local-python)
      * [Étape 5 : Configurer l'IDE Trae](#étape-5--configurer-lide-trae)
    * [macOS](#macos)
 * [😎 Restez à jour](#--restez-à-jour)

---

## Journal des modifications

### v1.1.1 (Dernière version)

- 🐛 **Correction d'un problème avec la fonction de modification des hosts** - Résolution d'un problème de caractère de saut de ligne anormal lors de la modification du fichier hosts

### v1.1.0

- ✨ **Nouvelle fonctionnalité de gestion des données utilisateur** - La version monofichier prend en charge le stockage persistant des données utilisateur
  - Emplacement de stockage des données : Windows `%APPDATA%\MTGA\`, macOS/Linux `~/.mtga/`
  - Prise en charge de la sauvegarde, de la restauration et de l'effacement des données utilisateur
  - Configuration, certificats SSL, sauvegarde des hosts automatiquement persistants
- 🔧 **Optimisation de la construction monofichier** - Amélioration de `build_onefile.bat`, prise en charge de la variable de numéro de version
- 🎯 **Amélioration de l'interface utilisateur** - Ajout d'un bouton d'actualisation de la liste des groupes de configuration, optimisation de la mise en page de l'interface
- 📖 **Documentation améliorée** - Ajout d'un guide de construction monofichier, mise à jour de la documentation du projet

### v1.0.0

- ✅ **Adaptation pour Mac OS** - Prise en charge de l'installation d'applications macOS  
- 🔄 **Changement de fournisseur par défaut** - Passage de DeepSeek à OpenAI  
- 📦 **Refactorisation des fichiers** - Renommage des fichiers liés à ds au format `*_ds.*` pour archivage  
- 🌐 **Modification du format de l'URL de l'API** - Passage de `https://your-api.example.com/v1` à `https://your-api.example.com`

---

## Démarrage rapide

### Utilisateurs Windows (méthode de lancement en un clic via l'interface graphique)

1. Téléchargez la dernière version de `MTGA_GUI-v{numéro de version}-x64.exe` depuis [GitHub Releases](https://github.com/BiFangKNT/mtga/releases)  
2. Double-cliquez sur le fichier exe téléchargé (des privilèges d'administrateur sont requis)  
3. Dans l'interface graphique ouverte, renseignez l'URL de l'API et l'ID du modèle  
   - **L'URL de l'API ne nécessite que le domaine (le numéro de port est optionnel, ne le renseignez pas si vous ne comprenez pas), sans la route suivante, par exemple : `https://your-api.example.com`**  
   - **Attention à bien distinguer le nom du modèle, ne le confondez pas avec les noms de modèles intégrés :**  
   - <img width="249" height="67" alt="differentiate model name" src="https://github.com/BiFangKNT/mtga/blob/gui/images/differentiate-model_name.png?raw=true" />  
4. Cliquez sur le bouton "Lancer tous les services en un clic"  
5. Attendez que le programme termine automatiquement les opérations suivantes :  
   - Génération et installation du certificat  
   - Modification du fichier hosts  
   - Démarrage du serveur proxy  
6. Une fois terminé, configurez votre IDE selon [Étape 5 : Configuration de Trae IDE](#第-5-步配置-trae-ide)

> [!NOTE]  
> - Un accès au pare-feu peut être requis lors du premier lancement  
> - La version mono-fichier prend en charge la persistance des données utilisateur, la configuration et les certificats sont sauvegardés automatiquement

### Utilisateurs macOS (installation via l'application)

#### Méthode d'installation

1. Téléchargez la dernière version de `MTGA_GUI-v{numéro de version}-aarch64.dmg` depuis [GitHub Releases](https://github.com/BiFangKNT/mtga/releases)  
2. Double-cliquez sur le fichier DMG, le système montera automatiquement le package d'installation  
3. Glissez-déposez `MTGA_GUI.app` dans le dossier `Applications`  
4. Lancez l'application depuis le Launchpad ou le dossier Applications

#### Mode d'emploi

1. Lancez `MTGA_GUI.app` (la première exécution peut nécessiter une autorisation dans les préférences système)
2. Dans l'interface graphique, renseignez :
   - **API URL** : l'adresse de votre service API (par exemple : `https://your-api.example.com`)
   - **ID du modèle** : nom personnalisé du modèle (évitez les conflits avec les modèles intégrés)
3. Cliquez sur le bouton "Lancer tous les services en un clic"
4. Le programme effectuera automatiquement :
   - La génération et l'installation du certificat SSL dans le trousseau système
   - La modification du fichier `/etc/hosts` (nécessite les privilèges administrateur)
5. Vous devez manuellement approuver le certificat généré dans la fenêtre du trousseau qui s'ouvre, nommé par défaut `MyLocalCA`
6. Démarrez le serveur proxy local
7. Suivez la configuration [Trae IDE ci-dessous](#第-5-步配置-trae-ide) pour finaliser la configuration

> **Remarques :**
> - La première exécution nécessite de saisir le mot de passe administrateur pour modifier les fichiers système
> - Il peut être nécessaire d'autoriser l'exécution de l'application dans "Préférences Système > Sécurité et confidentialité"
> - En cas de problème de permissions réseau, autorisez l'accès au réseau pour l'application dans "Préférences Système > Sécurité et confidentialité > Pare-feu"

---

## Lancement par script

### Étape 0 : Préparation de l'environnement

#### Windows

- Système Windows 10 ou supérieur
- Avoir les privilèges administrateur
- Installer l'environnement Python, version 3.10 ou supérieure recommandée
- Installer Git

##### Étape 1 : Générer un certificat auto-signé

Ouvrez Git Bash :

```bash
# 切换到 ca 目录
cd "mtga/ca"

# 1. 生成 CA 证书 (ca.crt 和 ca.key)
./genca.sh
```

Lors de l'exécution de `./genca.sh`, il vous demandera "Do you want to generate ca cert and key? [yes/no]", saisissez `y` et appuyez sur Entrée. Ensuite, il vous sera demandé de renseigner quelques informations :

*   `Country Name (2 letter code) []` : Saisissez `CN` (ou un autre code pays)
*   Les autres champs (comme State, Locality, Organization, Common Name for CA) peuvent être remplis au besoin ou laissés vides, il est recommandé de mettre `X`. Le Common Name peut être `MyLocalCA` ou similaire. L'e-mail peut être laissé vide.

```bash
# 2. 生成 api.openai.com 的服务器证书 (api.openai.com.crt 和 api.openai.com.key)
# 这个脚本会使用同目录下的 api.openai.com.subj 和 api.openai.com.cnf 配置文件
./gencrt.sh api.openai.com
```

Une fois l'exécution terminée, vous trouverez les fichiers importants suivants dans le répertoire `mtga\ca` :

*   `ca.crt` (votre certificat d'autorité de certification personnalisé)
*   `ca.key` (votre clé privée d'autorité de certification personnalisée - **ne pas divulguer**)
*   `api.openai.com.crt` (certificat SSL pour le serveur proxy local)
*   `api.openai.com.key` (clé privée SSL pour le serveur proxy local - **ne pas divulguer**)

##### Étape 2 : Faire confiance à votre certificat d'autorité de certification sous Windows

1.  Localisez le fichier `mtga\ca\ca.crt`.
2.  Double-cliquez sur le fichier `ca.crt` pour ouvrir la visionneuse de certificats.
3.  Cliquez sur le bouton "Installer le certificat...".
4.  Choisissez "Utilisateur actuel" ou "Ordinateur local". Il est recommandé de choisir "Ordinateur local" (cela nécessite les privilèges administrateur) pour que cela s'applique à tous les utilisateurs.
5.  Dans la boîte de dialogue suivante, sélectionnez "Placer tous les certificats dans le magasin suivant", puis cliquez sur "Parcourir...".
6.  Sélectionnez "Autorités de certification racines de confiance", puis cliquez sur "OK".
7.  Cliquez sur "Suivant", puis "Terminer". Si un avertissement de sécurité apparaît, choisissez "Oui".

##### Étape 3 : Modifier le fichier Hosts

**⚠️ AVERTISSEMENT : Après avoir effectué cette étape, vous ne pourrez plus accéder à l'API originale d'OpenAI. L'utilisation du site web n'est pas affectée.**

Vous devez modifier le fichier Hosts avec des privilèges d'administrateur pour pointer `api.openai.com` vers votre machine locale.

1.  Chemin du fichier Hosts : `C:\Windows\System32\drivers\etc\hosts`
2.  Ouvrez ce fichier en tant qu'administrateur avec le Bloc-notes (ou un autre éditeur de texte).
3.  Ajoutez la ligne suivante à la fin du fichier :
    ```
    127.0.0.1 api.openai.com
    ```
4.  Enregistrez le fichier.

##### Étape 4 : Exécuter le serveur proxy local (Python)

**Avant d'exécuter le serveur proxy :**

1.  **Installer les dépendances**:
    ```bash
    pip install Flask requests
    ```
2.  **Configurer le script**:
    *   Ouvrez le fichier `trae_proxy.py`.
    *   **Modifiez `TARGET_API_BASE_URL`** : Remplacez-la par l'URL de base de l'API au format OpenAI du site auquel vous souhaitez réellement vous connecter (par exemple : `"https://your-api.example.com"`).
    *   **Vérifiez les chemins des certificats** : Le script lit par défaut `api.openai.com.crt` et `api.openai.com.key` depuis `mtga\ca`. Si vos certificats ne se trouvent pas à cet emplacement, modifiez les valeurs de `CERT_FILE` et `KEY_FILE`, ou copiez ces deux fichiers dans le `CERT_DIR` spécifié par le script.

**Exécuter le serveur proxy :**

Ouvrez l'invite de commandes (cmd) ou PowerShell **en tant qu'administrateur** (car il faut écouter sur le port 443), puis exécutez :

```bash
python trae_proxy.py
```

Si tout se passe bien, vous devriez voir les journaux de démarrage du serveur.

##### Étape 5 : Configurer Trae IDE

1.  Ouvrez et connectez-vous à Trae IDE.
2.  Dans la boîte de dialogue IA, cliquez sur l'icône du modèle en bas à droite et sélectionnez "Ajouter un modèle" à la fin.
3.  **Fournisseur** : Sélectionnez `OpenAI`.
4.  **Modèle** : Sélectionnez "Modèle personnalisé".
5.  **ID du modèle** : Saisissez la valeur que vous avez définie pour `CUSTOM_MODEL_ID` dans le script Python (par exemple : `my-custom-local-model`).
6.  **Clé API** :
    *   Si votre API cible nécessite une clé API et que Trae la transmet via `Authorization: Bearer <key>`, alors la clé saisie ici sera transmise par le proxy Python.
    *   Lors de la configuration d'OpenAI dans Trae, la clé API est liée à la configuration `remove_reasoning_content`. Notre proxy Python ne gère pas cette logique, il se contente de transmettre l'en-tête Authorization. Vous pouvez essayer de saisir la clé requise par votre API cible, ou une clé arbitraire au format `sk-xxxx`.

7.  Cliquez sur "Ajouter un modèle".
8.  Revenez à la boîte de chat IA et sélectionnez le modèle personnalisé que vous venez d'ajouter dans le menu en bas à droite.

Maintenant, lorsque vous interagissez avec ce modèle personnalisé via Trae, les requêtes devraient passer par votre proxy Python local et être redirigées vers l'`TARGET_API_BASE_URL` que vous avez configuré.

**Conseils de dépannage :**

*   **Conflit de port** : Si le port 443 est déjà occupé (par exemple par IIS, Skype ou un autre service), le script Python échouera à démarrer. Vous devez arrêter le service qui utilise ce port, ou modifier le script Python et Nginx (si utilisé) pour écouter sur un autre port (mais cela est plus complexe, car Trae accède en dur au port 443 de `https://api.openai.com`).
*   **Pare-feu** : Assurez-vous que le pare-feu Windows autorise les connexions entrantes sur le port 443 pour Python (même s'il s'agit d'une connexion locale `127.0.0.1`, une configuration spéciale du pare-feu n'est généralement pas nécessaire, mais cela vaut la peine de vérifier).
*   **Problèmes de certificat** : Si Trae signale une erreur liée à SSL/TLS, vérifiez attentivement que le certificat d'autorité de certification (CA) est correctement installé dans les "Autorités de certification racines de confiance", et que le proxy Python charge correctement les fichiers `api.openai.com.crt` et `.key`.
*   **Journaux du proxy** : Le script Python imprime quelques journaux qui peuvent vous aider à diagnostiquer les problèmes.

Cette solution est plus intégrée que l'utilisation directe de vproxy + nginx, car elle place la terminaison TLS et la logique de proxy dans un seul script Python, ce qui la rend plus adaptée à la validation rapide de prototypes sur Windows.

#### macOS

-> [Méthode de démarrage par script pour Mac OS](https://github.com/BiFangKNT/mtga/blob/gui/docs/README_macOS_cli.md)

---

## 😎 Restez à jour

Cliquez sur les boutons Star et Watch en haut à droite du dépôt pour obtenir les dernières mises à jour.

![star to keep latest](https://github.com/BiFangKNT/mtga/blob/gui/images/star-to-keep-latest.gif?raw=true)

---

## Références

Le répertoire `ca` est référencé depuis le dépôt `wkgcass/vproxy`, merci au grand maître !