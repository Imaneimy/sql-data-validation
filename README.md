# 🔍 SQL Data Validation — Quality Reporting

> **Big Data Testing Project** | Python · SQLite/PostgreSQL · HTML Reports · Data Quality

---

## 🇫🇷 Description

Framework de validation de données SQL avec génération automatique de rapports qualité HTML et CSV.
Simule les contrôles réalisés sur un **DataMart** (dimensions + faits) avec 20 checks couvrant
complétude, unicité, plage de valeurs, intégrité référentielle et règles métier.

## 🇬🇧 Description

SQL data validation framework with automated HTML/CSV quality report generation.
Simulates checks performed on a **DataMart** (dimensions + facts) with 20 checks covering
completeness, uniqueness, value ranges, referential integrity, and business rules.

---

## 🗂️ Structure du projet

```
03_sql_data_validation/
├── src/
│   ├── checks/
│   │   └── sql_checks.py          # SQLQualityChecker — 8 types de contrôles
│   ├── reporters/
│   │   └── quality_reporter.py    # Génération rapports HTML + CSV
│   └── run_checks.py              # Orchestrateur — lance tous les checks
├── tests/
│   └── test_sql_checks.py         # TC-SQL-001 → TC-SQL-015
├── data/sql/
│   └── datamart.db                # Base SQLite (générée au lancement)
├── reports/
│   ├── quality_report.html        # Rapport visuel (généré)
│   └── quality_report.csv         # Export CSV (généré)
└── docs/
```

---

## 🧪 Types de contrôles

| Check | ID | Description |
|-------|----|----|
| `NOT NULL` | DQ-001, 002, 009, 011 | Colonnes obligatoires sans NULL |
| `UNIQUENESS` | DQ-003, 007, 010 | Clés primaires uniques |
| `VALUE RANGE` | DQ-008, 014, 015 | Montants et quantités positifs |
| `ALLOWED VALUES` | DQ-004, 016 | Valeurs dans un référentiel |
| `REFERENTIAL INTEGRITY` | DQ-012, 013 | FK → clés dimension existantes |
| `COMPLETENESS RATE` | DQ-017 | Taux de remplissage ≥ 95% |
| `ROW COUNT` | DQ-005, 018 | Volumétrie minimale |
| `CUSTOM SQL` | DQ-019 | `unit_price × quantity = total_amount` |
| `PATTERN MATCH` | DQ-020 | Format date `YYYY-MM-DD` |

---

## ⚙️ Installation & Exécution

```bash
pip install -r requirements.txt

# Lancer les checks + générer les rapports
cd src
python run_checks.py

# Ouvrir le rapport qualité
open ../reports/quality_report.html

# Tests unitaires
pytest tests/ -v
```

---

## 📊 Anomalies dans les données de test

| Anomalie | Check qui la détecte |
|---|---|
| `customer_id = NULL` (S009) | DQ-011 |
| Clé orpheline `C999` (S010) | DQ-012 |
| `total_amount = -59.98` (S011) | DQ-014 |
| `status = INVALID_STATUS` (S012) | DQ-016 |
| `unit_price × quantity ≠ total_amount` | DQ-019 |

---

## 📸 Aperçu du rapport HTML

Le rapport HTML généré affiche :
- Résumé avec compteurs pass/fail et taux de réussite
- Tableau détaillé avec code couleur (vert = PASS, rouge = FAIL)
- Badges de sévérité (HIGH / MEDIUM / LOW)

---

## 👩‍💻 Auteure

**Imane Moussafir** — Ingénieure Data & BI  
*Projet réalisé dans le cadre d'une candidature Testeur Big Data / Datalake.*
