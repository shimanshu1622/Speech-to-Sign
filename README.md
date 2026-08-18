# Real-Time Speech-to-Sign Language Interpreter

A modular real-time **Speech-to-Sign Language Interpreter** that converts spoken English into an intermediate ASL Gloss representation and maps the resulting gloss into sign/pose representations.

The project is designed as a modular pipeline so that individual components can be improved or replaced independently without affecting the rest of the system.

---

## 📌 Project Overview

While watching IPL, we noticed a small window where a person was translating commentary into sign language. This raised a simple question:

> Why can't this translation process be automated?    

To explore this idea, we developed a system that converts spoken English into a structured sign-language representation.

The long-term goal is to make the project **open-source** so that it can potentially be used across:

* Educational platforms
* News channels
* Live commentary
* Sports
* Video content
* Other accessibility-focused applications

---

## 🎯 Objective

The primary objective is to build a system capable of performing the following transformation:

```text
Speech
   ↓
Automatic Speech Recognition (ASR)
   ↓
NLP Processing
   ↓
English → ASL Gloss
   ↓
Gloss Normalization
   ↓
Gloss → Pose Mapping
   ↓
Skeletal Representation
```

The final output is a structured representation of sign-language movement that can be used by an avatar or other visualization system.

---

## 🏗️ System Architecture

The current system consists of **7 modular stages**:

```text
┌─────────────────┐
│  Speech Input   │
└────────┬────────┘
         ↓
┌─────────────────┐
│      ASR        │
│ faster-whisper  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ NLP Processing  │
│     spaCy       │
└────────┬────────┘
         ↓
┌─────────────────┐
│  LLM Gloss      │
│     Ollama      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Gloss Normalize │
│   LLM + Rules   │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Pose Mapping   │
│   Custom JSON   │
└────────┬────────┘
         ↓
┌─────────────────┐
│    Skeletal     │
│ Representation  │
└─────────────────┘
```

Each module has a specific responsibility and can be independently improved.

---

# 🔹 Module 1 — Speech Input

The first stage receives spoken English from the user.

Initially, recorded audio was used for testing.

The system was later extended toward **real-time audio input using WebSockets**.

### Input

```text
Human Speech
```

### Output

```text
Audio Stream
```

---

# 🔹 Module 2 — Automatic Speech Recognition

The ASR module converts audio into written English text.

### Initial Approach

The project initially used **Google Speech-to-Text** because of its easy integration and good baseline performance.

However, the cloud-based approach introduced problems such as:

* API latency
* Network dependency
* Inconsistent response time
* Performance variation based on network conditions

Therefore, the system was switched to **faster-whisper** for lower-latency and offline-capable processing.

### Technology

* faster-whisper
* Whisper
* CTranslate2

### Example

```text
Audio:
"I am going to school tomorrow"

        ↓ ASR

Text:
"I am going to school tomorrow"
```

---

# 🔹 Module 3 — NLP Processing

The ASR output may contain grammatical structures that are not directly suitable for semantic conversion into ASL Gloss.

Therefore, the text is processed using NLP techniques.

### Technology

* spaCy

### Main NLP Operations

#### 1. Tokenization

Break the sentence into individual tokens.

```text
"I went to school yesterday"

↓

["I", "went", "to", "school", "yesterday"]
```

#### 2. Lemmatization

Convert words into their base forms.

```text
going    → go
studying → study
went     → go
```

#### 3. Stop-word Identification

Certain words may not correspond directly to signs in ASL.

Examples:

```text
a
the
is
are
to
```

These words can be identified during preprocessing.

#### 4. Dependency Parsing

Dependency parsing helps identify grammatical relationships between words.

Example:

```text
Subject → I
Verb    → go
Object  → school
```

This helps the system understand the underlying structure of the sentence before generating ASL Gloss.

---

# 🔹 Module 4 — LLM-Based ASL Gloss Generation

The processed English text is converted into **ASL Gloss** using an LLM.

### Technology

* Ollama
* LLM-based prompting

The LLM receives the English sentence along with instructions for converting it into ASL-style gloss.

### Example

```text
English:

"I am going to school tomorrow."

        ↓

ASL Gloss:

"TOMORROW I GO SCHOOL"
```

The process focuses on extracting the semantic structure rather than performing a word-for-word translation.

---

## ASL Gloss Transformation

The system considers several linguistic transformations.

### 1. Subject–Verb–Object

```text
English:

I am going to school.

↓

I GO SCHOOL
```

### 2. Temporal Framing

Time references can be moved toward the beginning of the gloss.

```text
I am going to school tomorrow.

↓

TOMORROW I GO SCHOOL
```

### 3. Negation Restructuring

Negative constructions are transformed into a more appropriate gloss representation.

Example:

```text
I do not like this.

↓

I NOT LIKE THIS
```

---

# 🔹 Module 5 — Structured Gloss Normalization

LLM-generated gloss can still contain inconsistencies.

Therefore, a dedicated normalization stage is used.

This stage combines:

```text
LLM-based normalization
        +
Rule-based normalization
```

### Why Both?

The LLM provides:

* Context
* Semantic understanding
* Flexible restructuring

Rule-based processing provides:

* Grammar consistency
* Deterministic behavior
* Predictability
* Validation

This hybrid approach helps reduce inconsistencies in LLM-generated gloss.

---

# 🔹 Module 6 — Gloss-to-Pose Mapping

Once the gloss has been normalized, every gloss token needs to be mapped to an available sign representation.

### Mapping Approach

The project currently uses a **custom JSON-based mapping system**.

```text
GLOSS
  ↓
Sign Mapping
  ↓
Sign Representation
```

### Example

```text
YOU
  ↓
Corresponding sign representation
```

The mapping supports both manual and non-manual components.

### Manual Signs

Manual signs primarily involve:

* Hands
* Arms
* Body movements

### Non-Manual Signs

Non-manual components can include:

* Head movement
* Facial expressions
* Other facial/head-related information

---

## Fallback Mechanism

If a sign is not available for a particular gloss word, the system uses a fallback mechanism.

For example:

```text
Gloss:
YOU

Sign not found

        ↓

Fallback

        ↓

Y → O → U
```

The individual characters can then be represented using available finger-spelling signs.

This prevents the pipeline from completely failing when a particular word is not present in the sign database.

---

# 🔹 Module 7 — Skeletal Representation

The mapped signs are converted into a structured skeletal representation.

### Technology

* NumPy
* Custom kinematic logic

The system represents sign movement using **joint coordinates**.

```text
Sign
 ↓
Joint Coordinates
 ↓
Skeletal Structure
 ↓
3D Motion
 ↓
Avatar Animation
```

The output consists of:

* Joint coordinates
* Stick-figure/skeletal representation
* Animation-ready movement data

This representation can later be consumed by an avatar animation system.

---

# 🔄 Complete Example

Consider the input:

```text
"I am going to school tomorrow."
```

### Step 1 — Speech

```text
Audio Input
```

### Step 2 — ASR

```text
"I am going to school tomorrow."
```

### Step 3 — NLP

```text
Tokens:
[I, am, going, to, school, tomorrow]

Lemmatization:
go

Dependency structure:
I → go → school
```

### Step 4 — LLM Gloss Generation

```text
TOMORROW I GO SCHOOL
```

### Step 5 — Gloss Normalization

```text
TOMORROW I GO SCHOOL
```

Validated and normalized using the LLM + rule-based layer.

### Step 6 — Pose Mapping

```text
TOMORROW → Sign representation
I        → Sign representation
GO       → Sign representation
SCHOOL   → Sign representation
```

### Step 7 — Skeletal Representation

```text
Sign representations
        ↓
Joint coordinates
        ↓
Skeletal motion
        ↓
Animation
```

---

# ⚙️ Technology Stack

| Component               | Technology          |
| ----------------------- | ------------------- |
| Programming Language    | Python              |
| Speech Input            | Audio / WebSocket   |
| ASR                     | faster-whisper      |
| Speech Model            | Whisper             |
| NLP                     | spaCy               |
| LLM                     | Ollama              |
| Gloss Generation        | LLM + Prompting     |
| Gloss Normalization     | LLM + Rule-Based    |
| Pose Mapping            | Custom JSON Mapping |
| Skeletal Representation | NumPy               |
| Kinematics              | Custom Logic        |

---

# 📦 Pipeline Dependencies

```text
Python
 ├── faster-whisper
 ├── spaCy
 ├── Ollama
 ├── NumPy
 └── Custom Mapping / Kinematics
```

---

# 🚀 Real-Time Processing

The project is designed to support real-time speech processing.

The current input flow uses:

```text
Microphone
    ↓
WebSocket Audio Stream
    ↓
ASR
    ↓
NLP
    ↓
LLM
    ↓
Gloss Normalization
    ↓
Pose Mapping
    ↓
Skeletal Representation
```

The modular architecture allows each stage to be optimized independently for latency and accuracy.

---

# 🧩 Modular Design

One of the core design principles of the project is **modularity**.

```text
Speech
  ↓
ASR
  ↓
NLP
  ↓
LLM
  ↓
Normalization
  ↓
Mapping
  ↓
Skeletal Representation
```

Each module has a well-defined responsibility.

This allows us to replace or improve individual components without redesigning the complete pipeline.

For example:

```text
Google STT
    ↓
faster-whisper
```

The ASR implementation can be changed without changing the rest of the pipeline.

Similarly:

```text
LLM A
   ↓
LLM B
```

can be implemented without fundamentally changing the pose-mapping layer.

---

# 📈 Current Implementation

The current system has the following implemented/defined components:

* Speech input
* Real-time audio streaming approach
* Automatic Speech Recognition using faster-whisper
* NLP preprocessing using spaCy
* LLM-based English → ASL Gloss generation
* Gloss normalization
* Rule-based validation/normalization
* Custom gloss-to-sign mapping
* JSON-based sign mapping
* Fallback finger-spelling mechanism
* Skeletal representation
* Joint-coordinate representation
* Custom kinematic logic

---

# 🔮 Future Work

The project can be extended in several directions.

### Better ASL Translation

Improve English → ASL Gloss translation using:

* Larger datasets
* Better linguistic rules
* Fine-tuned language models
* Context-aware translation

### Expanded Sign Vocabulary

Increase the number of available signs and improve coverage for:

* Common vocabulary
* Technical terms
* Names
* Proper nouns
* Domain-specific vocabulary

### Improved Non-Manual Signs

Improve representation of:

* Facial expressions
* Head movement
* Eye gaze
* Body posture

### Real-Time Optimization

Reduce latency across:

```text
ASR → NLP → LLM → Mapping → Animation
```

### Avatar Animation

Use the skeletal representation to drive a 3D signing avatar.

### Production Deployment

For large-scale deployment, the modular pipeline can eventually be transformed into independently scalable services.

A possible architecture would use:

```text
Load Balancer
      ↓
Containerized Services
      ↓
Message Queue
      ↓
Independent ASR / NLP / LLM / Mapping Services
```

Possible technologies include:

* Docker
* Kubernetes
* Kafka / RabbitMQ
* JSON-based service communication
* Redis caching

High-load components such as ASR and LLM inference could be independently replicated.

---

# 🌍 Vision

The long-term vision is to create an **open-source, real-time speech-to-sign interpretation system** that can improve accessibility across different types of digital content.

Potential applications include:

```text
Educational Platforms
        ↓
News
        ↓
Sports Commentary
        ↓
Live Streams
        ↓
Video Content
        ↓
Accessibility Applications
```

---

# 👥 Project

**Project:** Real-Time Speech-to-Sign Language Interpreter

**Pipeline:**

```text
Speech
 → ASR
 → NLP
 → LLM Gloss Generation
 → Gloss Normalization
 → Pose Mapping
 → Skeletal Representation
```

The project is developed with a modular architecture to allow continuous improvement of individual components while maintaining the overall pipeline.
