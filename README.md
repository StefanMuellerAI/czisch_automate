# N8N ETL API

Eine modulare, dockerisierte OpenAPI mit drei n8n-kompatiblen Endpunkten für ETL-Operationen mit Playwright-Unterstützung.

## Features

- **Transform**: Umfassende Datenmanipulation und -transformation
- **Extract**: Datenextraktion aus verschiedenen Quellen (inkl. Web-Scraping)
- **Transfer**: Datenübertragung zu verschiedenen Zielsystemen
- **Playwright**: Integrierte Web-Automatisierung für Scraping
- **OpenAPI**: Vollständige API-Dokumentation
- **Docker**: Containerisiert für einfache Bereitstellung
- **Modulare Architektur**: Saubere Trennung von Services, Routers und Models

## Projektstruktur

```
czisch_automate/
├── app/
│   ├── __init__.py
│   ├── config.py              # Konfiguration und Settings
│   ├── models.py              # Pydantic-Modelle
│   ├── routers/               # API-Endpunkte
│   │   ├── __init__.py
│   │   ├── health.py          # Health Check
│   │   ├── transform.py       # Transform-Endpunkt
│   │   ├── extract.py         # Extract-Endpunkt
│   │   └── transfer.py        # Transfer-Endpunkt
│   └── services/              # Business Logic
│       ├── __init__.py
│       ├── playwright_service.py
│       ├── transform_service.py
│       ├── extract_service.py
│       └── transfer_service.py
├── main.py                    # FastAPI Entry Point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Schnellstart

### Mit Docker Compose (empfohlen)

```bash
# Repository klonen und ins Verzeichnis wechseln
cd czisch_automate

# Container bauen und starten
docker-compose up --build

# Im Hintergrund starten
docker-compose up -d --build
```

### Mit Docker

```bash
# Image bauen
docker build -t n8n-etl-api .

# Container starten
docker run -p 8000:8000 n8n-etl-api
```

### Lokal entwickeln

```bash
# Dependencies installieren
pip install -r requirements.txt

# Playwright Browser installieren
playwright install chromium

# Server starten
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API-Dokumentation

Nach dem Start ist die API verfügbar unter:

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API-Endpunkte

### Health Check
- `GET /` - Grundlegender Health Check
- `GET /status` - Detaillierter Status

### Transform-Endpunkt (`POST /transform`)

Umfassende Datenmanipulation mit verschiedenen Transformationsregeln:

**String-Transformationen:**
```json
{
  "data": "hello world",
  "transformation_rules": {
    "uppercase": true,
    "prefix": ">>> ",
    "suffix": " <<<",
    "replace": {"old": "world", "new": "universe"}
  }
}
```

**Numerische Transformationen:**
```json
{
  "data": 42,
  "transformation_rules": {
    "multiply": true,
    "multiply_by": 2,
    "add": true,
    "add_value": 10,
    "round": true,
    "decimal_places": 2
  }
}
```

**Dictionary-Transformationen:**
```json
{
  "data": {"name": "John", "age": 30, "city": "Berlin"},
  "transformation_rules": {
    "filter_keys": true,
    "allowed_keys": ["name", "age"],
    "add_timestamp": true
  }
}
```

### Extract-Endpunkt (`POST /extract`)

Datenextraktion aus verschiedenen Quellen:

**Web-Scraping:**
```json
{
  "source_url": "https://example.com",
  "extraction_config": {
    "selectors": {
      "title": "h1",
      "description": ".description"
    },
    "extract_meta": true,
    "extract_links": true
  }
}
```

**Datenfilterung:**
```json
{
  "source_data": [
    {"name": "Alice", "status": "active"},
    {"name": "Bob", "status": "inactive"}
  ],
  "extraction_config": {
    "extract_list": {
      "filter": {
        "field_equals": {"field": "status", "value": "active"}
      }
    }
  }
}
```

### Transfer-Endpunkt (`POST /transfer`)

Datenübertragung zu verschiedenen Zielsystemen:

**Webhook:**
```json
{
  "data": {"message": "Hello World"},
  "destination": "webhook",
  "transfer_config": {
    "webhook_url": "https://hooks.example.com/webhook",
    "method": "POST",
    "headers": {"Authorization": "Bearer token"}
  }
}
```

**Datei:**
```json
{
  "data": {"report": "data"},
  "destination": "file",
  "transfer_config": {
    "file_path": "/tmp/output.json",
    "format": "json",
    "append": false
  }
}
```

## Konfiguration

Die Anwendung kann über Umgebungsvariablen konfiguriert werden:

```bash
# API-Konfiguration
APP_NAME="N8N ETL API"
PORT=8000
DEBUG=false

# Playwright-Konfiguration
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000

# Logging
LOG_LEVEL=INFO
```

## Entwicklung und Erweiterung

### Neue Transformationen hinzufügen

1. Erweitern Sie `app/services/transform_service.py`
2. Fügen Sie neue Transformationslogik hinzu
3. Dokumentieren Sie die neuen Regeln in `app/routers/transform.py`

### Neue Extraktionsquellen

1. Erweitern Sie `app/services/extract_service.py`
2. Implementieren Sie neue Extraktionsmethoden
3. Aktualisieren Sie die Dokumentation

### Neue Transfer-Ziele

1. Erweitern Sie `app/services/transfer_service.py`
2. Implementieren Sie neue Transfer-Methoden
3. Fügen Sie entsprechende Konfigurationsmöglichkeiten hinzu

## Container-Management

```bash
# Logs anzeigen
docker-compose logs -f

# Container stoppen
docker-compose down

# Container neu bauen
docker-compose up --build

# Container-Status prüfen
docker-compose ps

# Einzelne Services neu starten
docker-compose restart n8n-etl-api
```

## Performance und Skalierung

- Playwright Browser wird beim Start initialisiert und wiederverwendet
- Asynchrone Verarbeitung für alle I/O-Operationen
- Modulare Architektur ermöglicht einfache Horizontal-Skalierung
- Health Checks für Load Balancer-Integration
