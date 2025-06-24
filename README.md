# AI Energy Scheduler

**AI-driven energischemaläggning för Home Assistant (2025.x)**

![Release](https://img.shields.io/badge/version-1.0.0-blue.svg)
![HACS](https://img.shields.io/badge/HACS%20compatible-green.svg)

## Innehållsförteckning

- [Funktioner](#funktioner)  
- [Installation](#installation)  
- [Config Flow](#config-flow)  
- [Service: set_schedule](#service-set_schedule)  
- [Service: cleanup_removed](#service-cleanup_removed)  
- [Exempel på JSON-schema](#exempel-på-json-schema)  
- [Entities som skapas](#entities-som-skapas)  
- [Exempel på ApexCharts-konfiguration](#exempel-på-apexcharts-konfiguration)  
- [Automations](#automations)  
- [Kalenderintegration](#kalenderintegration)  
- [Utveckling och testning](#utveckling-och-testning)  

---

## Funktioner

1. **JSON-baserad schemaläggning**  
   - Skicka in JSON via `ai_energy_scheduler.set_schedule` för att styra olika energilaster (värmepump, batteriladdning, elbil).  
   - Ingen statisk konfiguration – allt baseras på inkommande JSON.  
   - Validering mot `schema.json` med tydlig loggning.

2. **Automatisk entitetsskapande**  
   För varje enhet (device_id) i schemat skapas automatiskt:  
   - `sensor.ai_energy_scheduler_<device_id>_command`  
   - `sensor.ai_energy_scheduler_<device_id>_power_kw`  
   - `sensor.ai_energy_scheduler_<device_id>_energy_kwh`  
   - `sensor.ai_energy_scheduler_<device_id>_next_command`

3. **Sammanställningssensorer**  
   - `sensor.ai_energy_scheduler_total_power_kw`  
   - `sensor.ai_energy_scheduler_total_energy_kwh_today`  
   - `sensor.ai_energy_scheduler_last_update`

4. **Binär sensor**  
   - `binary_sensor.ai_energy_scheduler_alert` – visar ON om validering eller schemaläggning misslyckas.

5. **Kalenderintegration**  
   - `calendar.<device_id>` för varje enhet.  
   - Visa och redigera intervaller direkt i HA:s kalender-vy.  
   - Alla ändringar synkas till schemat och uppdaterar sensorer.

6. **Persistent lagring**  
   - Schemat sparas i `.storage/ai_energy_scheduler_data.json`.  
   - Klarar omstarter och återupptar föregående schema.

7. **Event-broadcasting**  
   - Integration skickar event `ai_energy_scheduler_schedule_updated` när nytt schema är sparat.  
   - Event `ai_energy_scheduler_command_activated` varje gång ett kommando aktiveras.  
   - Dessa events kan användas i automationer.

8. **HACS-stööd & CI**  
   - Installationsstöd via HACS (se `hacs.json`).  
   - GitHub Actions kör `hassfest`, `hacs validate` och `pytest`.  

---

## Installation

### 1) Via HACS

1. Öppna HACS i din Home Assistant  
2. Klicka på “Integrations” → “Utforska & Ladda upp ett nytt integration”  
3. Sök efter **AI Energy Scheduler**  
4. Installera, och klicka på “Konfigurera” när installationen är klar

### 2) Manuell installation

1. Ladda ner eller klona [https://github.com/robinostlund/ai_energy_scheduler](https://github.com/robinostlund/ai_energy_scheduler)  
2. Kopiera mappen `custom_components/ai_energy_scheduler` till `<config_dir>/custom_components/ai_energy_scheduler`  
3. Starta om Home Assistant

---

## Config Flow

Efter omstart går du till **Inställningar → Integrationer → Lägg till integration** och söker på “AI Energy Scheduler”.  
Du kan ge integrationen ett valfritt namn, men det är inte nödvändigt då allt styrs via service-anrop.

---

## Service: `ai_energy_scheduler.set_schedule`

Anropas när du vill skicka in ett nytt schema.  

- **Service**: `ai_energy_scheduler.set_schedule`  
- **Data**: Ett JSON-objekt enligt nedan.  
- **Exempel**:

```yaml
service: ai_energy_scheduler.set_schedule
data:
schedules: >
   {% set schedule = gpt_response.text %}
   {% set parsed = schedule | from_json %}
   {{ parsed }}
```