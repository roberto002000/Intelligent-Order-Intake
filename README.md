# 🤖 Intelligent Order Intake Pipeline

Pipeline intelligente per l'automazione del processo di acquisizione ordini in ambito manifatturiero.

Il progetto utilizza **Azure AI Foundry**, **Azure AI Document Intelligence**, **Python** e **Microsoft Fabric** per trasformare documenti PDF in dati strutturati pronti per l'analisi.

---

## 🚀 Tecnologie

- 🐍 Python
- 🤖 Azure AI Foundry
- 📄 Azure AI Document Intelligence
- ☁️ Microsoft Fabric
- ⚡ PySpark
- 📊 Power BI
- 🗄️ SQL
- 📁 JSON / CSV

---

## 🎯 Obiettivo

Ridurre tempi, errori e costi del processo di Order Intake attraverso una pipeline intelligente che:

- estrae automaticamente gli ordini dai PDF;
- valida clienti, articoli e prezzi;
- supporta l'operatore nelle revisioni;
- esporta i dati verso Microsoft Fabric.

---

## 🏗️ Architettura

```text
PDF
 │
 ▼
Azure AI Document Intelligence
 │
 ▼
Deterministic Orchestrator
 │
 ├── Request Router
 ├── Order Extractor
 ├── Review Assistant
 └── Commercial Responder
 │
 ▼
Order Validator
 │
 ├── ✅ Validated Orders (.json → .csv)
 └── ⚠️ Orders to Review (.json)
             │
             ▼
      Human Validation
```

---

## ⚙️ Workflow

1. 📄 Lettura del PDF tramite Azure AI Document Intelligence
2. 🧭 Classificazione della richiesta
3. 🤖 Attivazione dei soli agenti necessari
4. ✔️ Validazione deterministica
5. 📁 Esportazione:
   - JSON + CSV per ordini validati
   - JSON con suggerimenti AI per ordini da revisionare
6. ☁️ Caricamento su Microsoft Fabric

---

## 🧠 Agenti AI

| Agente | Funzione |
|---------|----------|
| 🧭 Request Router | Classifica il documento |
| 📦 Order Extractor | Estrae i dati dell'ordine |
| 🔍 Review Assistant | Analizza anomalie e propone correzioni |
| 💼 Commercial Responder | Gestisce richieste commerciali |

---

## 💰 Ottimizzazione dei costi

✔ Monitoraggio di input/output token

✔ Calcolo del costo per ogni chiamata

✔ Attivazione solo degli agenti necessari

✔ Orchestrazione deterministica

---

## 📊 Output

```
output/
├── ORDINE_VALIDATO/
│   ├── risultato.json
│   └── risultato.csv
│
└── RICHIESTA_REVISIONE/
    └── risultato.json
```

---

## 👨‍💻 Autore

**Roberto Iovino**
