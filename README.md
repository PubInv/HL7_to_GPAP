# HL7_to_GPAP

HL7 to GPAP bidirectional adapter

## What this project is

This project is a narrow Python MVP that bridges selected HL7 v2 ER7 messages and the Public Invention General Purpose Alarm Protocol (GPAP).

The immediate goal is not to solve all of HL7 alarm interoperability.

The immediate goal is to prove a working bridge that can:

- read a selected HL7 v2 ER7 message  
- extract alarm-like data from it  
- convert that data into a GPAP alarm string  
- optionally publish that GPAP alarm into an ADaM-style MQTT flow  
- wrap GPAP alarms and operator responses into custom HL7 Z messages for reverse transport  

This repo exists to make the bridge concrete, testable, and easy to evolve.

---

## Why this exists

Public Invention is building an open alarm ecosystem around GPAP, Krake, and ADaM.

HL7 is widely used in healthcare systems.

GPAP is intentionally compact and easy to parse.

A bridge between the two makes it possible to:

- receive alarm-like information from HL7-producing systems  
- convert that information into a format usable by ADaM and Krake-style components  
- preserve a path back into HL7-shaped messages when needed  

This makes the project useful for experimentation in clinical alarm management and other alarm-heavy domains.

---

## Current scope

This project currently supports a **narrow MVP profile**.

### Supported today

- Python package with a CLI  
- GPAP alarm parsing and rendering  
- GPAP operator response parsing and rendering  
- HL7 v2 ER7 text parsing with a simple segment splitter  
- conversion from a selected HL7 observation message into a GPAP alarm  
- conversion from a GPAP alarm into a custom HL7 Z message  
- conversion from a GPAP operator response into a custom HL7 Z message  
- optional MQTT publish step for ADaM-style integration  
- basic tests  

### Not supported yet

- full HL7 interoperability  
- FHIR  
- complete alarm semantics across all HL7 message types  
- full acknowledgment lifecycle with external clinical systems  
- production hardening  
- robust handling of many local hospital conventions  
- multi-OBX alarm correlation  
- standardized reverse mapping to an official alarm resource  

If you present this repo as a complete HL7 alarm solution, that is false.

This is an MVP bridge.

---

## Current bridge profile

The current HL7 to GPAP conversion uses a simple, explicit mapping.

### Incoming HL7 assumptions

The bridge expects HL7 v2 ER7 text and currently treats the first `OBX` segment as the alarm-carrying observation.

### Mapping used

- `MSH-10` → `alarm_id`  
- `MSH-3` → `source`  
- `PID-3` → `patient_id`  
- `OBX-3` → optional GPAP `alarm_type`  
- `OBX-8` → severity  
- `NTE-3` → preferred description  
- `OBX-5` → fallback description  
- default description → `HL7 alarm`  

### Severity mapping used in this MVP

- `N` → `1`  
- `L` → `2`  
- `LL` → `3`  
- `W` → `3`  
- `A` → `4`  
- `H` → `4`  
- `HH` → `5`  
- `AA` → `5`  

This mapping is heuristic and project-specific.

---

## GPAP format used here

```
a<severity>{message_id}[alarm_type]description
```

Where:

- `a` → alarm  
- `severity` → digit from 0–5  
- `{message_id}` → optional  
- `[alarm_type]` → optional  
- remaining text → description  

### Example

```
a5{MSG123}[15074]Pulse exceeded high-high threshold
```

### Operator actions

- `a` → acknowledge  
- `s` → shelve  
- `d` → dismiss  
- `c` → complete  

---

## Project layout

```
HL7_to_GPAP/
├── README.md
├── pyproject.toml
├── examples/
│   └── sample_oru.hl7
├── src/
│   └── hl7_to_gpap/
│       ├── __init__.py
│       ├── models.py
│       ├── gpap.py
│       ├── bridge.py
│       ├── mqtt.py
│       └── cli.py
└── tests/
    ├── test_gpap.py
    └── test_bridge.py
```

---

## Installation

```bash
py -m pip install -e .
```

If CLI is not on PATH:

```bash
py -m hl7_to_gpap.cli --help
```

---

## Example input

Create `examples/sample_oru.hl7`:

```
MSH|^~\&|MONITOR_APP|WARD1|ADAM|PUBINV|20260403113000||ORU^R01|MSG123|P|2.5
PID|1||PAT42^^^HOSP^MR||Doe^Jane
OBR|1||ORDER1|15074^Pulse^LN
OBX|1|NM|15074^Pulse^LN||180|bpm|60-100|HH|||F
NTE|1||Pulse exceeded high-high threshold
```

---

## Usage

### 1. HL7 → GPAP

```bash
py -m hl7_to_gpap.cli hl7-to-gpap --file examples/sample_oru.hl7
```

Output:

```
a5{MSG123}[15074]Pulse exceeded high-high threshold
```

---

### 2. GPAP → HL7 (alarm)

```bash
py -m hl7_to_gpap.cli gpap-to-hl7 --alarm "a5{MSG123}[15074]Pulse exceeded high-high threshold"
```

Output:

```
MSH|^~\&|GPAP_BRIDGE|PubInv|HL7_RECEIVER|PubInv|<timestamp>||ZGP^Z01|MSG123|P|2.5
ZAL|MSG123|5|15074|||Pulse exceeded high-high threshold
```

---

### 3. GPAP response → HL7

```bash
py -m hl7_to_gpap.cli response-to-hl7 --response "oc{MSG123}|sai|20260403120000"
```

Output:

```
MSH|^~\&|GPAP_BRIDGE|PubInv|HL7_RECEIVER|PubInv|<timestamp>||ZGP^Z02|MSG123|P|2.5
ZOP|MSG123|c|sai|20260403120000
```

---

### 4. HL7 → GPAP → MQTT

```bash
py -m hl7_to_gpap.cli publish-hl7 \
  --file examples/sample_oru.hl7 \
  --host public.cloud.shiftr.io \
  --port 1883 \
  --topic adam/in/alarms
```

---

## ADaM integration

Flow:

1. HL7 system emits ER7  
2. Bridge converts to GPAP  
3. Bridge publishes to MQTT  
4. ADaM consumes and processes alarms  

---

## Use cases

### Clinical alarm management

- Convert HL7 observations → GPAP alarms  
- Feed into ADaM/Krake pipeline  

### Other domains

- Market monitoring  
- IoT alerting systems  

---

## Design choices

### Why GPAP is simple

- Keeps downstream systems lightweight  
- Moves complexity into the bridge  

### Why custom HL7 Z messages

- No clean standard mapping exists in MVP  
- Explicit and honest approach  

---

## Testing

```bash
py -m pytest
```

### Covered

- GPAP parsing/rendering  
- HL7 → GPAP  
- GPAP → HL7  
- Operator responses  

---

## Known limitations

- First OBX only  
- Heuristic severity mapping  
- No deep HL7 modeling  
- Custom reverse mapping  
- MQTT is transport-only  

---

## Development priorities

- Configurable mappings  
- More HL7 support  
- Validation improvements  
- Integration tests  
- Possibly adopt `hl7apy`  

---

## Status

Early development.

This project proves architecture, not full standards compliance.

---

## License

AGPL-3.0

The protocol and integration points in that README are grounded in the current GPAP and ADaM repos, including ADaM’s MQTT-based flow and GPAP’s alarm structure with severity, optional message id, and optional alarm type. :contentReference[oaicite:1]{index=1}

Your original README is weak in three ways. It is too vague, it overpromises, and it does not explain the actual bridge behavior. This replacement fixes those problems.

The next thing you should do is replace the current README with this and then make sure the repo structure actually matches it.
::contentReference[oaicite:2]{index=2}