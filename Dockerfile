FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier uniquement le requirements.txt pour optimiser le cache Docker
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application
COPY . .

# Exposer le port par défaut utilisé par l'application
EXPOSE 8000

# Commande pour démarrer l'application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
