FROM python:3.9-slim

# VULNÉRABILITÉ: Exécution en tant que root (mauvaise pratique de sécurité)
USER root

# Configuration du répertoire de travail
WORKDIR /app

# Copie des fichiers de l'application
COPY app/ /app/

# Installation des dépendances avec versions vulnérables
RUN pip install --no-cache-dir -r requirements.txt

# VULNÉRABILITÉ: Permissions trop permissives
RUN chmod 777 /app

# Création de la base de données
RUN python -c "import sqlite3; conn = sqlite3.connect('products.db'); conn.close()"

# Exposition du port
EXPOSE 5000

# VULNÉRABILITÉ: Lancement de l'application avec debug=True en production
CMD ["python", "app.py"]
