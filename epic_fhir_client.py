"""
Epic FHIR Client
Fetches patient data from Epic FHIR API with pagination and rate limiting.
"""

import os
import time
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from epic_auth import EpicAuthClient

load_dotenv()


class EpicFHIRClient:
    """
    Client for fetching patient data from Epic FHIR API
    Handles pagination, rate limiting, and and multiple resource types.
    """

    def __init__(self):
        self.auth_client = EpicAuthClient()
        self.base_url = os.getenv("EPIC_FHIR_BASE_URL")

        if not self.base_url:
            raise ValueError("EPIC_FHIR_BASE_URL not found in .env file.")

        # Rate limiting: Epic typically allows ~10-20 requests per second
        self.min_request_interval = 0.1  # 10 requests per second
        self.last_request_time = 0

    def _wait_for_rate_limit(self):
        """
        Enforce rate liiting between requests

        :param self: Description
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to Epic FHIR API

        Args:
            url: Full FHIR resource URL
            params: Query parameters

        Returns:
            JSON response as a dictionary
        """
        self._wait_for_rate_limit()

        access_token = self.auth_client.get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/fhir+json",
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Handle rate limiting response
                print("Rate limit exceeded, retrying after 2 second delay...")
                time.sleep(2)
                return self._make_request(url, params)  # Retry request
            else:
                print(f"X HTTP Error {e.response.status_code}: {e.response.text}")
                raise
        except requests.exceptions.RequestException as e:
            print(f"X Request failed: {e}")
            raise

    def _fetch_with_pagination(
        self, resource_type: str, patient_id: str, params: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Fetch all pages of a resource type for a patient

        Args:
            resource_type: FHIR resource type (e.gl, "Condition", "MedicationRequest")
            patient_id: Patient ID
            params: Additional query parameters

        Returns:
            List of all resources entries across all pages
        """
        all_entries = []

        # Build initial URL
        url = f"{self.base_url}/{resource_type}"

        # Add patient search parameter
        if params is None:
            params = {}
        params["patient"] = patient_id
        params["_count"] = 50  # Number of results per page

        page_num = 1

        while url:
            print(f"  Fetching {resource_type} page {page_num}...")

            # Make request (only pass params on first request)
            if page_num == 1:
                data = self._make_request(url, params)
            else:
                data = self._make_request(url)

            # Extract entries
            entries = data.get("entry", [])
            all_entries.extend(entries)

            print(f". -> Got {len(entries)} entries (Total: {len(all_entries)})")

            # Check for next page
            url = None
            links = data.get("link", [])
            for link in links:
                if link.get("relation") == "next":
                    url = link.get("url")
                    page_num += 1
                    break
        return all_entries

    def get_patient(self, patient_id: str) -> Dict:
        """
        Fetch patient demographic information

        Args:
            patient_id: Patient ID

        Returns:
            Patient resource
        """
        print(f"\n Fetching Patient resource for {patient_id}...")
        url = f"{self.base_url}/Patient/{patient_id}"
        patient = self._make_request(url)
        print(f"Got patient: {patient.get('name', [{}])[0].get('text', 'Unknown')}")
        return patient

    def get_conditions(self, patient_id: str) -> List[Dict]:
        """
        Fetch all Condition resources for a patient

        Args:
            patient_id: Patient ID

        Returns:
            List of Condition resources
        """
        print(f"\n Fetching Condition resources for patient {patient_id}...")
        entries = self._fetch_with_pagination("Condition", patient_id)
        conditions = [entry["resource"] for entry in entries]
        print(f"Retrieved {len(conditions)} conditions.")
        return conditions

    def get_medications(self, patient_id: str) -> List[Dict]:
        """
        Fetch all MedicationRequest resources for a patient

        Args:
            patient_id: Patient ID

        Returns:
            List of MedicationRequest resources
        """
        print(f"\n Fetching MedicationRequest resources for patient {patient_id}...")
        entries = self._fetch_with_pagination("MedicationRequest", patient_id)
        medications = [entry["resource"] for entry in entries]
        print(f"Retrieved {len(medications)} medication requests.")
        return medications

    def get_observations(
        self, patient_id: str, category: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch all Observation resources for a patient, optionally filtered by category

        Args:
            patient_id: Patient ID
            category: Optional observation category (e.g., "vital-signs", "laboratory")

        Returns:
            List of Observation resources
        """
        print(f"\n Fetching Observation resources for patient {patient_id}...")
        params = {}
        if category:
            params["category"] = category
            print(f"Filtering by category: {category}")

        entries = self._fetch_with_pagination("Observation", patient_id, params)
        observations = [entry["resource"] for entry in entries]
        print(f"Retrieved {len(observations)} observations.")
        return observations

    def get_all_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """
        Fetch all relevant FHIR resources for a patient

        Args:
            patient_id: Patient ID
        Returns:
            Dictionary containing all patient data organized by resource type
        """
        print("=" * 60)
        print(f"Fetching all data for patient {patient_id}")
        print("=" * 60)

        data = {
            "patient_id": patient_id,
            "patient": self.get_patient(patient_id),
            "conditions": self.get_conditions(patient_id),
            "medications": self.get_medications(patient_id),
            "observations": self.get_observations(patient_id),
        }

        print("\n" + "=" * 60)
        print(" Data fetch complete!")
        print("=" * 60)
        print(f"Patient: {data["patient"].get("name", [{}])[0].get("text", "Unknown")}")
        print(f"Conditions: {len(data["conditions"])}")
        print(f"Medications: {len(data["medications"])}")
        print(f"Observations: {len(data["observations"])}")
        print("=" * 60)

        return data


def test_fhir_client():
    """
    Test the FHIR client with a test patient

    """
    test_patient_id = os.getenv("TEST_PATIENT_ID", "example-patient-id")
    try:
        client = EpicFHIRClient()

        # Fetch all data for the test patient
        patient_data = client.get_all_patient_data(test_patient_id)

        # Display sample condition
        if patient_data["conditions"]:
            print("\n Sample Condition:")
            condition = patient_data["conditions"][0]
            code = condition.get("code", {}).get("coding", [{}])[0]
            print(f"- {code.get('display', 'Unknown Condition')}")

        # Display sample medication
        if patient_data["medications"]:
            print("\n Sample Medication:")
            med = patient_data["medications"][0]
            med_code = med.get("medicationCodeableConcept", {}).get("coding", [{}])[0]
            print(f"- {code.get('display', 'Unknown Medication')}")

    except Exception as e:
        print(f"\n X Test failed: {e}")
        raise


if __name__ == "__main__":
    test_fhir_client()
