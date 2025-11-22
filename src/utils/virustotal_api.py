"""
VirusTotal API integration
"""
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse


class VirusTotalAPI:
    """VirusTotal API client for URL analysis"""

    API_URL = "https://www.virustotal.com/api/v3/urls"
    API_URL_ID = "https://www.virustotal.com/api/v3/urls/{url_id}"

    def __init__(self, api_key: str):
        """
        Initialize VirusTotal API client

        Args:
            api_key: VirusTotal API key
        """
        self.api_key = api_key
        self.headers = {
            "x-apikey": api_key,
            "accept": "application/json"
        }

    def analyze_url(self, url: str) -> Dict[str, Any]:
        """
        Analyze a URL with VirusTotal

        Args:
            url: URL to analyze

        Returns:
            Analysis results dictionary with URL analysis
        """
        try:
            import base64
            import time

            # Calculate URL ID correctly (base64url encode without padding)
            url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")

            # Try to get existing report first
            existing_report = self.get_url_report(url_id)

            # If report doesn't have error, return it
            if "error" not in existing_report:
                return existing_report

            # If report has error (not found), submit new scan
            if "404" in str(existing_report.get("error", "")) or "NotFoundError" in str(existing_report.get("error", "")):
                # Submit URL for scanning
                response = requests.post(
                    self.API_URL,
                    headers=self.headers,
                    data={"url": url},
                    timeout=30
                )

                if response.status_code == 200:
                    # Wait for scan to complete
                    time.sleep(5)
                    # Get report using the URL ID (not analysis ID)
                    url_report = self.get_url_report(url_id)
                    return url_report
                else:
                    return {
                        "error": f"Scan submission failed (status {response.status_code})",
                        "details": response.text
                    }

            # Return the error from the existing report
            return existing_report

        except requests.exceptions.Timeout:
            return {"error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def get_url_report(self, url_id: str) -> Dict[str, Any]:
        """
        Get URL analysis report

        Args:
            url_id: URL ID from VirusTotal

        Returns:
            Analysis report dictionary
        """
        try:
            response = requests.get(
                self.API_URL_ID.format(url_id=url_id),
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_report(data)
            else:
                return {
                    "error": f"Failed to get report (status {response.status_code})",
                    "details": response.text
                }

        except Exception as e:
            return {"error": f"Failed to get report: {str(e)}"}

    def _parse_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse VirusTotal API response

        Args:
            data: Raw API response

        Returns:
            Parsed report dictionary
        """
        try:
            attributes = data.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})
            results = attributes.get("last_analysis_results", {})

            # Extract domain info
            url = attributes.get("url", "N/A")
            last_analysis_date = attributes.get("last_analysis_date")
            if last_analysis_date:
                analysis_date = datetime.fromtimestamp(last_analysis_date).strftime("%Y-%m-%d %H:%M:%S")
            else:
                analysis_date = "N/A"

            # Calculate detection ratio
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            undetected = stats.get("undetected", 0)
            harmless = stats.get("harmless", 0)
            total = malicious + suspicious + undetected + harmless

            # Note: WHOIS data from VirusTotal URL endpoint is often empty
            # Use APILayer for reliable WHOIS lookups instead
            whois_dict = {}

            # Get detected engines
            detected_engines = []
            for engine, result in results.items():
                if result.get("category") in ["malicious", "suspicious"]:
                    detected_engines.append({
                        "engine": engine,
                        "category": result.get("category"),
                        "result": result.get("result", "N/A")
                    })

            return {
                "url": url,
                "analysis_date": analysis_date,
                "stats": {
                    "malicious": malicious,
                    "suspicious": suspicious,
                    "undetected": undetected,
                    "harmless": harmless,
                    "total": total
                },
                "detection_ratio": f"{malicious}/{total}",
                "detected_engines": detected_engines[:10],  # Top 10
                "whois": whois_dict,
                "reputation": attributes.get("reputation", 0),
                "categories": attributes.get("categories", {}),
                "error": None
            }

        except Exception as e:
            return {"error": f"Failed to parse report: {str(e)}"}

    def test_api_key(self) -> tuple[bool, str]:
        """
        Test if API key is valid

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Test by submitting a known good URL
            response = requests.post(
                self.API_URL,
                headers=self.headers,
                data={"url": "https://www.google.com"},
                timeout=10
            )

            if response.status_code == 200:
                return True, "API key is valid"
            elif response.status_code == 401:
                return False, "Invalid API key (status 401)"
            elif response.status_code == 403:
                return False, "Access forbidden - check API key permissions (status 403)"
            elif response.status_code == 429:
                # Rate limit means the key works but quota is exhausted
                return True, "API key is valid (rate limited)"
            else:
                return False, f"API test failed with status {response.status_code}"

        except Exception as e:
            return False, f"API test failed: {str(e)}"
