# 🌀 Lüftungssteuerung für Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/DEIN_GITHUB_NAME/ha-lueftung.svg)](https://github.com/DEIN_GITHUB_NAME/ha-lueftung/releases)

Custom Integration für Home Assistant zur Steuerung von Lüftungsanlagen über die SEC Smart API.

## Features

- 🌡️ **Temperaturregelung** – automatische Lüftungssteuerung bei Grenzwertüberschreitung
- 💧 **Feuchtigkeitsregelung** – automatische Steuerung bei zu hoher/niedriger Luftfeuchtigkeit
- 🌙 **Nachtmodus** – definierbare Zeitfenster mit reduzierter Lüftungsstufe
- 🎛️ **6 unabhängige Bereiche** – jeder Bereich einzeln steuerbar
- 📱 **Eigenes UI-Panel** – direkt in der HA-Sidebar integriert
- 💾 **Persistente Regeln** – Einstellungen bleiben nach Neustart erhalten

## Installation via HACS

1. HACS öffnen → **Integrationen** → Drei-Punkte-Menü oben rechts → **Benutzerdefinierte Repositories**
2. URL eingeben: `https://github.com/DEIN_GITHUB_NAME/ha-lueftung`
3. Kategorie: **Integration** → Hinzufügen
4. Integration suchen: „Lüftungssteuerung" → Installieren
5. Home Assistant neu starten
6. **Einstellungen → Integrationen → + Hinzufügen → Lüftungssteuerung**

## Manuelle Installation

1. Ordner `custom_components/lueftung/` nach `<config>/custom_components/lueftung/` kopieren
2. Home Assistant neu starten
3. **Einstellungen → Integrationen → + Hinzufügen → Lüftungssteuerung**

## Konfiguration

Beim Setup werden folgende Angaben benötigt:

| Feld | Beschreibung |
|------|-------------|
| Geräte-ID | ID deiner Lüftungsanlage (z.B. `9D0324`) |
| API Token | Bearer Token der SEC Smart API |
| Abfrage-Intervall | Wie oft der Status abgefragt wird (Standard: 120s) |

## Unterstützte Modi

`Fans off` · `Manual 1–6` · `Boost ventilation` · `Humidity regulation` · `CO2 regulation` · `Timed program` · `Snooze` · `INACTIVE`

## Versionen

| Version | Änderungen |
|---------|-----------|
| 2.0.0 | Komplette Neugestaltung, Automatisierungs-Engine, UI-Panel |
| 1.0.0 | Initiale Version |
