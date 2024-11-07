#!/bin/bash

# Configuration
PYTHON_PATH="/Users/arnaud/Desktop/arnaud ici/DataFusionCatalogManager"
VENV_PATH="venv"
LOG_DIR="logs"
API_PORT=8530
ADMIN_PORT=8531
FRONTEND_PORT=8532

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Création du répertoire de logs
mkdir -p $LOG_DIR

# Fonction pour le logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Vérification de l'environnement virtuel
if [ ! -d "$VENV_PATH" ]; then
    log "Création de l'environnement virtuel..."
    python3 -m venv $VENV_PATH
fi

# Activation de l'environnement virtuel
source $VENV_PATH/bin/activate

# Installation/Mise à jour des dépendances
log "Mise à jour des dépendances..."
pip install -r requirements.txt

# Arrêt des services existants
log "Arrêt des services existants..."
pkill -f streamlit
pkill -f uvicorn

# Vérification de la base de données
if [ ! -f "catalog.db" ]; then
    warning "Base de données non trouvée, initialisation..."
    python -c "from models.database import Base, engine; Base.metadata.create_all(bind=engine)"
fi

# Démarrage des services
log "Démarrage du backend API..."
PYTHONPATH=$PYTHON_PATH uvicorn api.subscription_api:app --host 0.0.0.0 --port $API_PORT > $LOG_DIR/api.log 2>&1 &
API_PID=$!

log "Démarrage de l'interface admin..."
PYTHONPATH=$PYTHON_PATH streamlit run main.py --server.port $ADMIN_PORT > $LOG_DIR/admin.log 2>&1 &
ADMIN_PID=$!

log "Démarrage du frontend..."
PYTHONPATH=$PYTHON_PATH streamlit run frontend_app.py --server.port $FRONTEND_PORT > $LOG_DIR/frontend.log 2>&1 &
FRONTEND_PID=$!

# Vérification des services
sleep 5

check_service() {
    local port=$1
    local name=$2
    if nc -z localhost $port; then
        log "$name est en cours d'exécution sur le port $port"
        return 0
    else
        error "$name n'a pas démarré correctement sur le port $port"
        return 1
    fi
}

# Vérification des services
check_service $API_PORT "Backend API"
check_service $ADMIN_PORT "Interface Admin"
check_service $FRONTEND_PORT "Frontend"

# Affichage des URLs
echo ""
log "Services démarrés avec succès!"
echo "URLs des services:"
echo "Backend API:     http://localhost:$API_PORT/docs"
echo "Interface Admin: http://localhost:$ADMIN_PORT"
echo "Frontend:        http://localhost:$FRONTEND_PORT"
echo ""
log "Logs disponibles dans le répertoire $LOG_DIR"
echo ""

# Fonction pour arrêter proprement les services
cleanup() {
    log "Arrêt des services..."
    kill $API_PID 2>/dev/null
    kill $ADMIN_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Capture du signal d'arrêt
trap cleanup SIGINT SIGTERM

# Maintenir le script en vie
log "Appuyez sur Ctrl+C pour arrêter tous les services"
while true; do
    sleep 1
done
