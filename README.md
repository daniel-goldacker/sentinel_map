# SentinelMap (FastAPI + WebSocket + Leaflet)

Mapa defensivo em tempo real para visualizar eventos suspeitos com geolocalizacao de IP.

## Estrutura

```text
.
|-- src/
|   |-- application.py          # rotas FastAPI e WebSocket
|   |-- config.py               # configuracoes e paths
|   |-- geoip_service.py        # lookup GeoIP
|   |-- schemas.py              # modelos Pydantic
|   `-- state.py                # estado e metricas em memoria
|-- scripts/
|   `-- event_simulator.py      # simulador principal
|-- data/
|   `-- GeoLite2-City.mmdb
`-- static/
    |-- index.html
    |-- css/dashboard.css
    `-- js/dashboard.js
```

## 1) Instalar dependencias

```powershell
pip install -r requirements.txt
```

## 2) GeoIP (MaxMind)

1. Baixe o `GeoLite2-City.mmdb` no site da MaxMind.
2. Coloque o arquivo em `data/GeoLite2-City.mmdb`.

Obs.: O projeto já inclui um arquivo `data/GeoLite2-City.mmdb` para facilitar os testes. Se quiser dados mais atualizados, basta substituir esse arquivo por uma versão mais recente.


## 3) Rodar backend

```powershell
uvicorn --app-dir src application:app --reload --reload-dir src --reload-dir static --host 0.0.0.0 --port 8000
```

Abra: `http://localhost:8000`

## 4) Endpoints

- `GET /` -> dashboard
- `GET /health` -> status
- `GET /stats` -> metricas agregadas
- `POST /event` -> ingestao
- `WS /ws` -> stream em tempo real

## 5) Simular eventos

```powershell
python scripts/event_simulator.py --count 200 --interval 0.2
```

## 6) Exemplo de chamada de API de negocio (sem ip no body)

```powershell
curl.exe -X POST http://localhost:8000/event `
  -H "Content-Type: application/json" `
  -H "X-Forwarded-For: 203.0.113.10" `
  -d "{\"type\":\"transacao_negada\",\"path\":\"/api/v1/pagamentos/autorizar\",\"ua\":\"erp-backend/2.1\"}"
```
