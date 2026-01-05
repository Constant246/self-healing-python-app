#!/usr/bin/env python3
import subprocess
import time 
import json
import os
import shutil
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# --- 1. CONFIGURATION SÉCURISÉE ---
# Charge la clé API depuis le fichier .env protégé
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ Erreur : GEMINI_API_KEY non trouvée dans le fichier .env")
    exit(1)

# Configuration de l'IA Gemini
# --- Configuration de l'IA Gemini ---
genai.configure(api_key=GEMINI_API_KEY)

# On cherche automatiquement un modèle "flash" disponible dans votre liste
available_models = [m.name for m in genai.list_models() if 'flash' in m.name]

if not available_models:
    # Si aucun flash n'est trouvé, on essaie un nom standard par défaut
    SELECTED_MODEL = 'gemini-1.5-flash' 
else:
    # On prend le premier modèle "flash" de la liste (ex: gemini-2.5-flash...)
    SELECTED_MODEL = available_models[0]

print(f"🤖 Modèle sélectionné : {SELECTED_MODEL}")
model = genai.GenerativeModel(SELECTED_MODEL)

class AISecurityBrain:
    def __init__(self):
        self.root_path = Path(".")
        self.app_path = Path("app")
        self.report_file = Path("trivy-report.json")
        self.secure_app_path = Path("app_secure")
        
    def apply_git_workflow(self, cve_id, file_path):
        """Module 4 : Automatisation de la remédiation via Git"""
        branch_name = f"fix/{cve_id.lower()}"
        
        try:
            # 1. Créer et basculer sur une nouvelle branche pour cette faille
            subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True, text=True)
            
            # 2. Ajouter le fichier corrigé à l'index Git
            subprocess.run(["git", "add", file_path], check=True, capture_output=True, text=True)
            
            # 3. Valider avec un message de commit professionnel
            commit_message = f"security: fix vulnerability {cve_id}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, text=True)
            
            print(f"🌿 Branche créée et commit effectué : {branch_name}")
            
            # 4. Revenir sur la branche principale pour la prochaine correction
            # Remplacez 'main' par 'master' si votre branche s'appelle master
            subprocess.run(["git", "checkout", "main"], check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Erreur Git (branche déjà existante ?) : {e.stderr}")    
        
    def load_report(self):
        """Charge le diagnostic de sécurité généré par GitHub/Trivy"""
        if not self.report_file.exists():
            print(f"❌ Erreur : {self.report_file} est introuvable. Téléchargez-le depuis GitHub Actions.")
            return None
        with open(self.report_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_ai_fix(self, vuln_id, title, description, file_path, original_code):
        """Demande à l'IA Gemini de générer un code corrigé"""
        print(f"🤖 Appel à l'IA pour corriger : {vuln_id} ({title})")
        
        prompt = f"""
        Tu es un expert en cybersécurité spécialisé en Python et Flask.
        Une faille a été détectée dans le fichier : {file_path}
        
        DÉTAILS DE LA FAILLE :
        - ID : {vuln_id}
        - Titre : {title}
        - Description : {description}

        CODE SOURCE ACTUEL :
        ```python
        {original_code}
        ```

        CONSIGNES DE CORRECTION :
        1. Corrige la faille mentionnée en utilisant les meilleures pratiques (ex: requêtes paramétrées pour SQLi).
        2. Utilise 'os.getenv()' pour remplacer tout secret ou clé API en dur.
        3. Ne modifie pas la logique métier de l'application.
        4. Renvoie UNIQUEMENT le code Python complet et corrigé, sans aucune explication ni balises Markdown.
        """
        
        try:
            response = model.generate_content(prompt)
            # Nettoyage de la réponse pour ne garder que le code
            clean_code = response.text.replace("```python", "").replace("```", "").strip()
            return clean_code
        except Exception as e:
            print(f"⚠️ Erreur lors de l'appel à Gemini : {e}")
            return None

    def run(self):
        print("🧠 Démarrage du Cerveau IA - Analyse et Correction...")
        
        # 1. Charger le rapport
        report_data = self.load_report()
        if not report_data:
            return

        # 2. Préparer le dossier sécurisé (Copie fraîche de l'existant)
        if self.secure_app_path.exists():
            shutil.rmtree(self.secure_app_path)
        shutil.copytree(self.app_path, self.secure_app_path)
        print(f"📁 Dossier de travail créé : {self.secure_app_path}")

        # 3. Parcourir les résultats du rapport Trivy
        for result in report_data.get('Results', []):
            target_file_relative = result.get('Target') # ex: app/app.py
            
            if 'Vulnerabilities' in result:
                # On récupère le chemin réel du fichier pour le lire
                # Si le rapport dit 'app/app.py', on l'ouvre
                try:
                    with open(target_file_relative, 'r', encoding='utf-8') as f:
                        current_code = f.read()
                    
                    # Pour chaque vulnérabilité dans ce fichier
                    for vuln in result['Vulnerabilities']:
                        fixed_code = self.get_ai_fix(
                            vuln.get('VulnerabilityID'),
                            vuln.get('Title'),
                            vuln.get('Description'),
                            target_file_relative,
                            current_code
                        )
                        
                        if fixed_code:
                            # On sauvegarde la version corrigée dans app_secure
                            # Note : On prend juste le nom du fichier (app.py)
                            filename = Path(target_file_relative).name
                            save_path = self.secure_app_path / filename
                            
                            with open(save_path, 'w', encoding='utf-8') as f:
                                f.write(fixed_code)
                            
                            # On met à jour current_code pour la prochaine vulnérabilité du même fichier
                            current_code = fixed_code
                            print(f"✅ Correction appliquée dans {save_path}")
                            
                            # --- AJOUT MODULE 4 : Gestion Git ---
                            self.apply_git_workflow(vuln.get('VulnerabilityID'), save_path)
                            # -------------------------------------
                            
                            # --- AJOUT DE LIGNE POUR RESPECTER LE QUOTA ---
                            print("⏳ Pause de 5 secondes pour respecter le quota (offre gratuite)...")
                            time.sleep(5)
                            

                except Exception as e:
                    print(f"❌ Impossible de traiter le fichier {target_file_relative} : {e}")

        print("\n✨ Mission terminée ! Les fichiers corrigés sont dans le dossier 'app_secure'.")

if __name__ == "__main__":
    brain = AISecurityBrain()
    brain.run()
