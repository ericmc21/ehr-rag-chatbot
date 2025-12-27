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
            context_parts.append(f"[{metadata['resource_type']}]\n{doc}\n")

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
            temperature=0.7,
            max_tokens=500,
        )

        return response.choices[0].message.content

    def chat(
        self, query: str, patient_id: str, conversation_history: List[Dict[str, str]]
    ) -> tuple[str, str]:
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


def init_session_state():
    """Initialize Streamlit session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []  # List of dicts with 'role' and 'content'
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = PatientChatbot()
    if "patient_id" not in st.session_state:
        st.session_state.patient_id = os.getenv(
            "TEST_PATIENT_ID", "eq081-VQEgP8drUUqCWzHfw3"
        )


def display_chat_history():
    """Display chat message history"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def main():
    """
    Main Streamlit app function
    """
    st.set_page_config(page_title="EHR Patient Chatbot", page_icon="🏥", layout="wide")

    # Initialize session state
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.title("🏥 EHR Patient Chatbot")
        st.markdown("---")

        st.subheader("Configuration")

        # Patient ID selector
        patient_id = st.text_input(
            "Patient ID",
            value=st.session_state.patient_id,
            help="Enter the patient ID to query",
        )
        st.session_state.patient_id = patient_id

        # Collection stats
        st.markdown("---")
        st.subheader("📊 Database Stats")
        try:
            stats = st.session_state.chatbot.embedding_pipeline.get_collection_stats()
            st.metric("Total Documents", stats["total_documents"])
            st.metric("Collection", stats["collection_name"])
        except Exception as e:
            st.error(f"Failed to load database stats: {e}")

        # Clear chat button
        st.markdown("---")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

        # Info
        st.markdown("---")
        st.markdown(
            """
        ### How to use
        1. Enter a patient ID (or use default)
        2. Ask questions about the patient's:
              - Medical sonditions
              - Medications
              - Observations (labs, vitals)
              - General health information
                    
        ### Example Questions
        - What conditions does this patient have?
        - What medications is the patient taking?
        - What were the most recent lab results?
        - Summarize the patient's health status."""
        )

    # Main chat interface
    st.title("💬 Chat with Patient Records")
    st.markdown(f"**Current Patient:** `{st.session_state.patient_id}`")

    # Display chat history
    display_chat_history()

    # Chat input
    if prompt := st.chat_input("Ask a question about the patient's records..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response, context = st.session_state.chatbot.chat(
                        query=prompt,
                        patient_id=st.session_state.patient_id,
                        conversation_history=st.session_state.messages,
                    )
                    st.markdown(response)

                    # Show retrieved context in expander
                    with st.expander("📋 View Retrieved Context"):
                        st.text(context)

                    # Add assistant response to chat history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )

                except Exception as e:
                    st.error(f"Error generating response: {e}")
                    st.exception(e)


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ OPENAI_API_KEY not found in environment variables")
        st.stop()
    main()
