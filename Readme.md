# EHR Data Chatbot with RAG (Epic FHIR)

A chatbot that integrates with Epic's FHIR API to query patient data using RAG (Retrieval Augmented Generation).

## Features

- ✅ Epic FHIR authentication (Backend Service with JWT)
- 🔄 Patient data retrieval (Patient, Condition, MedicationRequest, Observation)
- 📊 Vector database indexing (ChromaDB/Pinecone)
- 💬 Streamlit chatbot interface
- ⚡ Rate limiting and pagination handling

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

# Edit .env with your Epic credentials:
# - EPIC_CLIENT_ID: From your Epic app registration
# - EPIC_KEY_ID: The 'kid' from your JWKS (found in generate_jwks.py output)
# - Update other values if Epic's URLs differ
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

You should see:

```
Testing Epic FHIR Authentication
✓ Access token obtained (expires in 3600s)
✓ Successfully authenticated!
```

## Epic App Registration Checklist

- [ ] Created Backend System app in Epic App Orchard
- [ ] Generated RSA key pair and JWKS
- [ ] Hosted JWKS on GitHub Pages
- [ ] Added JWKS URL to Epic app
- [ ] Requested scopes: patient/Patient.read, patient/Condition.read, patient/MedicationRequest.read, patient/Observation.read
- [ ] Got Client ID from Epic
- [ ] Noted test patient IDs from Epic documentation

## Next Steps

1. **Test authentication** - Run `python epic_auth.py`
2. **Build FHIR client** - Fetch patient data with pagination/rate limiting
3. **Set up vector database** - Index patient data in ChromaDB
4. **Build chatbot** - Create Streamlit interface

## Project Structure

```
ehr-rag-chatbot/
├── epic_auth.py          # Authentication module
├── epic_fhir_client.py   # FHIR data fetching (next)
├── embedding_pipeline.py # Vector indexing (next)
├── app.py                # Streamlit chatbot (next)
├── requirements.txt
├── .env                  # Your credentials (not in git)
├── .env.example          # Template
└── private_key.pem       # Your private key (not in git)
```

## Resources

- [Epic FHIR Documentation](https://fhir.epic.com/)
- [Epic Test Patients](https://fhir.epic.com/Documentation?docId=testpatients)
- [SMART Backend Services](http://hl7.org/fhir/smart-app-launch/backend-services.html)
