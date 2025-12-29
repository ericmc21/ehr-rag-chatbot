# EHR Data Chatbot with RAG (Epic FHIR)

A production-ready RAG-powered chatbot that integrates with Epic's FHIR API to query patient medical records using natural language.

## Key Features

- ✅ **Real EHR Integration** - Connects to Epic's FHIR API with OAuth 2.0 JWT authentication
- ✅ **Multi-Patient Support** - Index and query multiple patients from a single database
- ✅ **Comprehensive Data Retrieval** - Fetches Patient demographics, Conditions, Medications, and Observations
- ✅ **Vector Search** - Semantic search over medical records using ChromaDB
- ✅ **RAG-Powered AI** - Context-aware responses using GPT-4 with retrieved medical context
- ✅ **Interactive UI** - Streamlit chat interface with patient switching and source citations
- ✅ **Production Ready** - Handles pagination, rate limiting, and error recovery

## Demo

Ask natural language questions like:

- "What chronic conditions does this patient have?"
- "List all medications the patient is currently taking"
- "What were the blood pressure readings in the last year?"
- "Summarize the patient's overall health status"

The chatbot retrieves relevant medical records and generates accurate, context-aware responses.

## Architecture

```
Epic FHIR API → Data Client → Embedding Pipeline → ChromaDB
                                                        ↓
                                              Streamlit Chatbot
                                                        ↓
                                                  OpenAI GPT-4
```

## Setup

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your credentials:
# - EPIC_CLIENT_ID: From your Epic app registration
# - EPIC_KEY_ID: The 'kid' from your JWKS
# - OPENAI_API_KEY: From OpenAI platform
# - TEST_PATIENT_ID_LIST: Comma-separated list of Epic test patient IDs
```

Example `.env` configuration:

```bash
EPIC_CLIENT_ID=your_client_id
EPIC_KEY_ID=your_key_id
OPENAI_API_KEY=sk-proj-...
TEST_PATIENT_ID_LIST=eq081-VQEgP8drUUqCWzHfw3,erXuFYUfucBZaryVksYEcMg3,eNTjHHFchfetalizEr3nBUw3
```

### 3. Add Your Private Key

```bash
# Copy the private_key.pem you generated earlier into this directory
# NEVER commit this file to git!
```

### 4. Test Authentication

```bash
python epic_auth.py
```

### 5. Test FHIR Client

```bash
python epic_fhir_client.py
```

### 6. Index Patient Data

```bash
python index_patient.py
```

This fetches and indexes **all patients** listed in `TEST_PATIENT_ID_LIST` from Epic into ChromaDB. The script will loop through each patient and create embeddings for their medical records.

### 7. Launch Chatbot

```bash
streamlit run app.py
```

The chatbot will open in your browser at `http://localhost:8501`

## Usage

### Querying Multiple Patients

The chatbot supports querying across multiple indexed patients:

1. Use the **Patient ID selector** in the sidebar to switch between patients
2. Or manually enter any indexed patient ID
3. The chatbot will filter search results to only that patient's records

### Example Questions

- "What medical conditions does this patient have?"
- "What medications is the patient currently taking?"
- "What were the most recent lab results?"
- "Summarize the patient's health status"
- "Does the patient have diabetes?"
- "What is the patient's blood pressure trend?"

### Indexing Additional Patients

To add more patients to your database:

**Option 1: Update .env and re-run**

```bash
# Add patient IDs to TEST_PATIENT_ID_LIST in .env
TEST_PATIENT_ID_LIST=patient1,patient2,patient3,new_patient4

# Re-run indexing (only new patients will be added)
python index_patient.py
```

**Option 2: Programmatically**

```python
from index_patient import index_patient

# Index individual patients
index_patient("patient_id_1")
index_patient("patient_id_2")
```

**Note:** The ChromaDB collection stores all patients together, but filters by `patient_id` during search to maintain data isolation.

## Project Structure

```
ehr-rag-chatbot/
├── epic_auth.py          # Epic OAuth authentication
├── epic_fhir_client.py   # FHIR data fetching
├── embedding_pipeline.py # Vector embeddings & ChromaDB
├── app.py                # Streamlit chatbot UI
├── index_patient.py      # Helper to index patient data
├── requirements.txt
├── .env                  # Your credentials (not in git)
├── .env.example          # Template
├── private_key.pem       # Your private key (not in git)
└── chroma_db/            # ChromaDB storage (not in git)
```

## How It Works

### 1. Authentication

Uses JWT-based OAuth 2.0 client credentials flow:

- Signs JWT with your private RSA key
- Exchanges JWT for access token from Epic
- Tokens cached and refreshed automatically

### 2. Data Retrieval

Fetches FHIR resources with pagination and rate limiting:

- Patient demographics
- Conditions (diagnoses)
- MedicationRequests (prescriptions)
- Observations (labs, vitals)

### 3. Embedding & Indexing

Converts FHIR data to searchable vectors:

- Processes each resource into readable text
- Generates embeddings with OpenAI's `text-embedding-3-small`
- Stores in ChromaDB for semantic search

### 4. RAG Chat

Retrieval Augmented Generation workflow:

- User asks a question
- Retrieves relevant patient records via semantic search
- Passes context to GPT-4 to generate accurate answer
- Cites source records in response

## Epic App Registration Checklist

- [ ] Created Backend System app in Epic App Orchard
- [ ] Generated RSA key pair and JWKS
- [ ] Hosted JWKS on GitHub Pages
- [ ] Added JWKS URL to Epic app
- [ ] Requested scopes: `system/Patient.read`, `system/Condition.read`, `system/MedicationRequest.read`, `system/Observation.read`
- [ ] Got Client ID from Epic
- [ ] Noted test patient IDs from Epic documentation

## API Keys Required

1. **Epic FHIR** - Free sandbox access at https://fhir.epic.com
2. **OpenAI** - Get API key at https://platform.openai.com/api-keys

## Troubleshooting

### 403 Forbidden Error

- Check that you have `system/*.read` scopes (not `patient/*.read`)
- Wait 2-3 minutes after adding scopes for changes to propagate
- Restart script to get fresh token

### 400 Bad Request on Observations

- Epic requires `category` parameter for Observation searches
- Code automatically defaults to "vital-signs" category

### ChromaDB Errors

- Delete `chroma_db/` directory and re-index if database becomes corrupted
- Make sure you have write permissions in project directory

## Resources

- [Epic FHIR Documentation](https://fhir.epic.com/)
- [Epic Test Patients](https://fhir.epic.com/Documentation?docId=testpatients)
- [SMART Backend Services](http://hl7.org/fhir/smart-app-launch/backend-services.html)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
