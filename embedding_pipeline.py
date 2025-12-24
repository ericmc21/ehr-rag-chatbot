"""
Embedding Pipeline for FHIR Data
Processes patient data, generates embeddings, and indexes in ChromaDB
"""

import os
import json
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings
from openai import OpenAI

load_dotenv()


class FHIRDocumentProcessor:
    """
    Processes FHIR patient data into documents for embedding
    """

    @staticmethod
    def process_patient(patient: Dict) -> str:
        """
        Convert Patient resource to text
        """
        name = patient.get("name", [{}])[0].get("text", "Unknown")
        gender = patient.get("gender", "Unknown")
        birth_date = patient.get("birthDate", "Unknown")

        return f"Patient: {name}\nGender: {gender} \nBirth Date: {birth_date}"

    @staticmethod
    def process_conditions(condition: Dict) -> str:
        """
        Convert Condition resource to text
        """
        code = condition.get("code", {}).get("text", "Unknown Condition")
        coding = condition.get("code", {}).get("coding", [{}])[0]
        display = coding.get("display", "Unknown Condition")
        onset = condition.get("onsetDateTime", "Unknown Onset Date")
        clinical_status = condition.get("clinicalStatus", {}).get(
            "text", "Unknown Status"
        )

        text = f"Condition: {display}\n"
        text += f"Status: {clinical_status}\n"
        text += f"Onset Date: {onset}\n"

        return text

    @staticmethod
    def process_observation(observation: Dict) -> str:
        """
        Convert Observation resource to text
        """
        code = observation.get("code", {}).get("text", "Unknown Observation")
        coding = observation.get("code", {}).get("coding", [{}])[0]
        display = coding.get("display", "Unknown Observation")
        value = observation.get("valueQuantity", {}).get("value", "Unknown Value")
        unit = observation.get("valueQuantity", {}).get("unit", "")
        value_text = (
            f"{value} {unit}".strip()
            if value and unit
            else observation.get("valueString", "No value")
        )
        effective_date = observation.get("effectiveDateTime", "Unknown Date")

        text = f"Observation: {display}\n"
        text += f"Value: {value_text}\n"
        text += f"Date: {effective_date}"

        return text


class FHIREmbeddingPipeline:
    """
    Generates embeddings and stores in ChromaDB
    """

    def __init__(self, collection_name: str = "patient_records"):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db", settings=Settings(anonymized_telemetry=False)
        )

        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

        self.processor = FHIRDocumentProcessor()

        print(f" Initialized CrhomaDB collection: {collection_name} ")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for given text using OpenAI's text-embedding-3-small model

        Args:
            text: Input text to embed

        Returns:
            Embedding vector
        """
        response = self.opoenai_client.embeddings.create(
            model="text-embedding-3-small", input=text
        )
        return response.data[0].embedding

    def index_patient_data(self, patient_data: Dict[str, Any]) -> int:
        """
        Process and index all patient data in ChromaDB

        Args:
            patient_data: Dictionary from EpicFHIRClient.get_all_patient_data()

        Returns:
            Number of documents indexed
        """
        patient_id = patient_data["patient_id"]

        print("=" * 60)
        print(f"Indexing data for patient {patient_id}")
        print("=" * 60)

        documents = []
        metadatas = []
        ids = []

        # Process patient demographics
        print("\n Processing patient demographics...")
        patient_text = self.processor.process_patient(patient_data["patient"])
        documents.append(patient_text)
        metadatas.append(
            {
                "type": "patient",
                "patient_id": patient_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        ids.append(f"{patient_id}_patient")

        # Process conditions
        print(f"\n Processing {len(patient_data["conditions"])} conditions.")
        for idx, condition in enumerate(patient_data["conditions"]):
            condition_text = self.processor.process_conditions(condition)
            documents.append(condition_text)

            condition_id = condition.get("id", f"condition_{idx}")
            metadatas.append(
                {
                    "patient_id": patient_id,
                    "resource_type": "Condition",
                    "resource_id": condition_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            ids.append(f"{patient_id}_condition_{condition_id}")

        # Process medications
        print(f" Processing {len(patient_data["medications"])} medications.")
        for idx, medication in enumerate(patient_data["medications"]):
            med_text = self.processor.process_medication(medication)
            documents.append(med_text)

        med_id = medication.get("id", f"medication_{idx}")
        metadatas.append(
            {
                "patient_id": patient_id,
                "resource_type": "MedicationRequest",
                "resource_id": med_id,
                "timestamp": datetime.now().isoformat(),
            }
        )
        ids.append(f"{patient_id}_medication_{med_id}")

        # Process observations
        obs_sample = patient_data["observations"][:50]
        print(
            f"Processing {len(obs_sample)} observations (sampled from {len(patient_data["observations"])})..."
        )
        for idx, observation in enumerate(obs_sample):
            obs_text = self.processor.process_observation(observation)
            documents.append(obs_text)

            obs_id = observation.get("id", f"observation_{idx}")
            metadatas.append(
                {
                    "patient_id": patient_id,
                    "resource_type": "Observation",
                    "resource_id": obs_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            ids.append(f"{patient_id}_observation_{obs_id}")

        # Generate embeddings and add to ChromaDB
        print(f"Generating embeddings for {len(documents)} documents...")
        embeddings = []
        for i, doc in enumerate(documents):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(documents)} ")
                embedding = self.generate_embedding(doc)
                embeddings.append(embedding)

        print("Adding documents to ChromaDB collection...")
        self.collection.add(
            documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids
        )

        print("=" * 60)
        print(f" Indexed {len(documents)} documents for patient {patient_id} ")
        print("=" * 60)

        return len(documents)
    def search(self, query: str, n_results: int = 5, patient_id: Optional[str]) -> Dict:
        """
        Search for relevant documents in ChromaDB

        Args:
            query: Search query text
            n_results: Number of results to return
            patient_id: Filter results by patient ID

        Returns:
            Search results from ChromaDB
        """
        # Generate embedding for the query
        query_embedding = self.generate_embedding(query)

        # Build where filter
        where_filter = None
        if patient_id:
            where_filter = {"patient_id": patient_id}
        
        # Search
        results = self.collection.query(query_embeddings=[query_embedding],n_results=n_results,where=where_filter)
        return results
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the ChromaDB collection

        Returns:
            Collection statistics
        """
        count = self.collection.count()
        return {
            "total_documents": count,
            "collection_name": self.collection.name,
        }
        