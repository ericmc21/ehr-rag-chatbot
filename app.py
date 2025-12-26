"""
Streamlit Chatbot for Querying Patient EHR Data
Uses RAG (Retrieval-Augmented Generation) to answer questions based on patient data with ChromaDB
"""

import streamlit as st
import os
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI

from embedding_pipeline import EmbeddingPipeline

load_dotenv()


class PatientChatbot:
    """
    RAG-based chatbot for patient data querires
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_pipeline = EmbeddingPipeline()

    def retrieve_context(self, query: str, patient_id: str, n_results: int = 5) -> str:
        """
        Retrieve relevant context from ChromaDB

        Args:
            query: User query
            patient_id: Patient ID to filter results
            n_results: Number of context results to retrieve

        Returns:
            Formatted context string
        """
        results = self.embedding_pipeline.search(
            query=query, n_results=n_results, patient_id=patient_id
        )

        # Format retreived documents
        context_parts = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            context_parts.append(f"[{metadata["resource_type"]}]\n{doc}\n")

        return "\n\n".join(context_parts)

    def generate_response(
        self, query: str, context: str, conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Generate response using OpenAI with retrieved context

        Args:
            query: User query
            context: Retrieved context
            conversation_history: List of previous messages in the conversation
        Returns:
            AI generated response
        """
        # Build system message with context
        system_message = f"""You are a helpful medical assistant analyzing patient health records.

        Use the following patient information to answer questions accurately:

        {context}

        Guidelines:
        - Answer based only on the provided patient data.
        - If the answer is not in the data, respond with "I don't know based on the provided information."
        - Keep answers concise and relevant.
        - Use medical terminology appropriately but explain when needed
        - Cite which type of record you're referencing (e.g., "According to patient's conditions...")
        """

        # Build messages for API
        messages = [{"role": "system", "content": system_message}]

        # add conversation history (last 5 exchanges to keep context manageable)
        for msg in conversation_history:
            messages.append(msg)

        # Add current query
        messages.append({"role": "user", "content": query})

        # Generate response
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
            max_tokens=500,
        )

        return response.choices[0].message.content
    
    def chat(self, query: str, patient_id: str, conversation_history: List[Dict[str, str]]) -> tuple[str, str]:
        """
        Main chat function combining retrieval and generation

        Args:
            query: User query
            patient_id: Patient ID
            conversation_history: List of previous messages in the conversation
        Returns:
            Tuple of (response string, retrieved context)
        """
        # Retrieve relevant context
        context = self.retrieve_context(query, patient_id)

        # Generate response
        response = self.generate_response(query, context, conversation_history)

        return response, context
    
    
