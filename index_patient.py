"""
Helper script to index patient data before using the chatbot
"""

import os
from dotenv import load_dotenv
from epic_fhir_client import EpicFHIRClient
from embedding_pipeline import EmbeddingPipeline

load_dotenv()


def index_patient(patient_id: str):
    """
    Fetch and index a patient's data

    Args:
        patient_id: Patient ID to index
    """
    print("=" * 60)
    print(f"Indexing Patient: {patient_id}")
    print("=" * 60)

    # Fetch patient data from Epic
    print("\n1️⃣ Fetching patient data from Epic FHIR API...")
    fhir_client = EpicFHIRClient()
    patient_data = fhir_client.get_all_patient_data(patient_id)

    # Initialize embedding pipeline
    print("\n2️⃣ Initializing embedding pipeline...")
    pipeline = EmbeddingPipeline()

    # Index the data
    print("\n3️⃣ Generating embeddings and indexing...")
    num_docs = pipeline.index_patient_data(patient_data)

    print("\n" + "=" * 60)
    print(f"✅ Successfully indexed {num_docs} documents for patient {patient_id}")
    print("=" * 60)
    print("\n💡 You can now run the chatbot with:")
    print("   streamlit run app.py")
    print("=" * 60)


def main():
    """Main function"""
    # Get patient ID from environment variable
    patient_id_list = os.getenv("TEST_PATIENT_ID_LIST", "eq081-VQEgP8drUUqCWzHfw3")
    # Index all patients
    patient_ids = patient_id_list.split(",")

    if not patient_id_list:
        print("❌ TEST_PATIENT_ID not found in .env file")
        print("\nPlease add to your .env:")
        print("TEST_PATIENT_ID=your_patient_id_here")
        return

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in .env file")
        print("\nPlease add to your .env:")
        print("OPENAI_API_KEY=sk-...")
        return

    try:
        for patient_id in patient_ids:
            index_patient(patient_id)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
