"""
IP2WHOIS API integration
"""
import requests
from typing import Dict, Any


class IP2WHOISAPI:
    """IP2WHOIS API client"""

    API_URL = "https://api.ip2whois.com/v2"

    def __init__(self, api_key: str):
        """
        Initialize IP2WHOIS API client

        Args:
            api_key: IP2WHOIS API key
        """
        self.api_key = api_key

    def get_whois(self, domain: str) -> Dict[str, Any]:
        """
        Get WHOIS information for a domain

        Args:
            domain: Domain name to query

        Returns:
            Dictionary with WHOIS data
        """
        try:
            params = {
                "key": self.api_key,
                "domain": domain
            }
            response = requests.get(
                self.API_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_whois(data)
            else:
                return {
                    "error": f"Failed to get WHOIS (status {response.status_code})",
                    "details": response.text
                }

        except requests.exceptions.Timeout:
            return {"error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _parse_whois(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse IP2WHOIS API response

        Args:
            data: Raw API response

        Returns:
            Parsed WHOIS dictionary
        """
        try:
            # Debug: Print all available fields from API
            print(f"DEBUG: IP2WHOIS raw result keys: {list(data.keys())}")

            whois_dict = {}

            # Domain
            if data.get("domain"):
                whois_dict["Domain"] = data["domain"]

            # Dates
            if data.get("create_date"):
                whois_dict["Creation Date"] = data["create_date"]

            if data.get("update_date"):
                whois_dict["Updated Date"] = data["update_date"]

            if data.get("expire_date"):
                whois_dict["Expiration Date"] = data["expire_date"]

            # Domain age in years
            if data.get("domain_age"):
                age_days = data["domain_age"]
                age_years = round(age_days / 365.25, 1)
                whois_dict["Domain Age"] = f"{age_years} years ({age_days} days)"

            # Name servers
            if data.get("nameservers") and isinstance(data["nameservers"], list):
                whois_dict["Name Servers"] = ", ".join(data["nameservers"])

            # Registrar
            registrar = data.get("registrar", {})
            if registrar and isinstance(registrar, dict):
                if registrar.get("name"):
                    whois_dict["Registrar"] = registrar["name"]

            # Registrant - include ALL fields
            registrant = data.get("registrant", {})
            if registrant and isinstance(registrant, dict):
                # Only add non-empty fields
                if registrant.get("name"):
                    whois_dict["Registrant Name"] = registrant["name"]
                if registrant.get("organization"):
                    whois_dict["Registrant Organization"] = registrant["organization"]
                if registrant.get("street_address"):
                    whois_dict["Registrant Address"] = registrant["street_address"]
                if registrant.get("city"):
                    whois_dict["Registrant City"] = registrant["city"]
                if registrant.get("region"):
                    whois_dict["Registrant Region"] = registrant["region"]
                if registrant.get("zip_code"):
                    whois_dict["Registrant Zip"] = registrant["zip_code"]
                if registrant.get("country"):
                    whois_dict["Registrant Country"] = registrant["country"]
                if registrant.get("phone"):
                    whois_dict["Registrant Phone"] = registrant["phone"]
                if registrant.get("fax"):
                    whois_dict["Registrant Fax"] = registrant["fax"]
                if registrant.get("email"):
                    whois_dict["Registrant Email"] = registrant["email"]

            # Admin - include ALL fields
            admin = data.get("admin", {})
            if admin and isinstance(admin, dict):
                # Only add non-empty fields
                if admin.get("name"):
                    whois_dict["Admin Name"] = admin["name"]
                if admin.get("organization"):
                    whois_dict["Admin Organization"] = admin["organization"]
                if admin.get("street_address"):
                    whois_dict["Admin Address"] = admin["street_address"]
                if admin.get("city"):
                    whois_dict["Admin City"] = admin["city"]
                if admin.get("region"):
                    whois_dict["Admin Region"] = admin["region"]
                if admin.get("zip_code"):
                    whois_dict["Admin Zip"] = admin["zip_code"]
                if admin.get("country"):
                    whois_dict["Admin Country"] = admin["country"]
                if admin.get("phone"):
                    whois_dict["Admin Phone"] = admin["phone"]
                if admin.get("fax"):
                    whois_dict["Admin Fax"] = admin["fax"]
                if admin.get("email"):
                    whois_dict["Admin Email"] = admin["email"]

            # Status
            if data.get("status"):
                # Clean up status (remove URLs)
                status = data["status"]
                if "https://" in status:
                    status = status.split("https://")[0].strip()
                whois_dict["Status"] = status

            return whois_dict

        except Exception as e:
            return {"error": f"Failed to parse WHOIS: {str(e)}"}

    def test_api_key(self) -> tuple[bool, str]:
        """
        Test if API key is valid

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Test with a common domain
            result = self.get_whois("google.com")

            if "error" in result:
                error_msg = result.get("error", "")
                if "401" in str(result.get("details", "")) or "Invalid" in error_msg:
                    return False, "Invalid API key"
                return False, result["error"]

            return True, "API key is valid"

        except Exception as e:
            return False, f"API test failed: {str(e)}"
