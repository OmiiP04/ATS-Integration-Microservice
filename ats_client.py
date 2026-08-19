import os
import requests
import base64
import json

class GreenhouseClient:
    def __init__(self):
        self.api_key = os.environ.get('ATS_API_KEY')
        self.base_url = os.environ.get('ATS_BASE_URL', 'https://harvest.greenhouse.io/v1')
        self.on_behalf_of = os.environ.get('ON_BEHALF_OF') # Greenhouse often requires this header for some actions
        
        # Greenhouse Basic Auth uses API Key as username, blank password
        if self.api_key:
            auth_str = f'{self.api_key}:'
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            self.headers = {
                'Authorization': f'Basic {b64_auth}',
                'Content-Type': 'application/json'
            }
            if self.on_behalf_of:
                self.headers['On-Behalf-Of'] = self.on_behalf_of
        else:
            self.headers = {'Content-Type': 'application/json'}
            print("WARNING: No ATS_API_KEY provided. Switching to MOCK MODE.")
            self.mock_mode = True

        if self.api_key and self.api_key != "YOUR_GREENHOUSE_API_KEY":
             self.mock_mode = False
        else:
             self.mock_mode = True
             print("MOCK MODE ENABLED: Returning dummy data.")

    def get_jobs(self):
        """
        Fetch jobs from Greenhouse and normalize them.
        Greenhouse Harvest API: GET /jobs
        """
        try:
            if getattr(self, 'mock_mode', False):
                return [
                    {"id": "mock-1", "title": "Software Engineer (Mock)", "location": "Remote", "status": "OPEN", "external_url": "http://example.com/job/1"},
                    {"id": "mock-2", "title": "Product Manager (Mock)", "location": "New York", "status": "OPEN", "external_url": "http://example.com/job/2"}
                ]

            # By default getting open jobs. 
            # Note: In a real scenario, could implement pagination loop here.
            response = requests.get(f"{self.base_url}/jobs?status=open", headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Basic pagination handling: Fetch all pages
            jobs = []
            url = f"{self.base_url}/jobs?status=open"
            
            while url:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Greenhouse returns a list directly for /jobs
                current_jobs = data
                
                for job in current_jobs:
                    # Normalization
                    jobs.append({
                        "id": str(job.get('id')),
                        "title": job.get('name'),
                        "location": job.get('offices')[0].get('name') if job.get('offices') else "Remote/Unspecified",
                        "status": job.get('status').upper(),
                        "external_url": job.get('absolute_url') or ""
                    })
                
                # Check for Link header for pagination (Greenhouse uses Link headers)
                # Format: <https://harvest.greenhouse.io/v1/jobs?page=2&per_page=100>; rel="next"
                link_header = response.headers.get('Link')
                url = None # Reset
                if link_header:
                    links = link_header.split(',')
                    for link in links:
                        if 'rel="next"' in link:
                            url = link[link.find("<")+1 : link.find(">")]
                            break
            
            return jobs
        except requests.exceptions.RequestException as e:
            print(f"Error fetching jobs: {e}")
            # Identify if it's 401/403 etc
            raise e

    def create_candidate(self, payload):
        """
        Create a candidate in Greenhouse and attach to job.
        Greenhouse Harvest API: POST /candidates
        """
        # 1. First create the candidate
        # Mapping generic payload to Greenhouse payload
        gh_payload = {
            "first_name": payload.get('name').split(' ')[0],
            "last_name": " ".join(payload.get('name').split(' ')[1:]) if ' ' in payload.get('name') else "",
            "email_addresses": [{"value": payload.get('email'), "type": "personal"}],
            "phone_numbers": [{"value": payload.get('phone'), "type": "mobile"}]
        }
        
       
        # Handling resume/website if needed - Greenhouse is complex with attachments.
        # For this simple demo, we'll strip resume_url or add it as a website/link if possible
        if payload.get('resume_url'):
            gh_payload['website_addresses'] = [{"value": payload.get('resume_url'), "type": "portfolio"}]

        try:
            if getattr(self, 'mock_mode', False):
                return {
                    "id": "mock-candidate-123",
                    "message": "Candidate created and applied successfully (MOCK)"
                }

            # Create Candidate
            response = requests.post(f"{self.base_url}/candidates", json=gh_payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            candidate_data = response.json()
            candidate_id = candidate_data.get('id')

            # 2. Attach to Job (Create Application)
            # Greenhouse Harvest API: POST /candidates/{id}/applications
            job_id = payload.get('job_id')
            if job_id:
                app_payload = {
                    "job_id": int(job_id)
                }
                app_response = requests.post(f"{self.base_url}/candidates/{candidate_id}/applications", json=app_payload, headers=self.headers, timeout=10)
                app_response.raise_for_status()
                # application_data = app_response.json()
            
            return {
                "id": str(candidate_id),
                "message": "Candidate created and applied successfully"
            }

        except requests.exceptions.RequestException as e:
            print(f"Error creating candidate: {e}")
            # If 400, might be validation error
             # In a real app we'd parse response.text for details
            raise e

    def get_applications(self, job_id):
        """
        List applications for a given job.
        Greenhouse Harvest API: GET /applications?job_id=...
        """
        try:
            if getattr(self, 'mock_mode', False):
                 return [
                    {"id": "mock-app-1", "candidate_name": "John Doe (Mock)", "email": "john@example.com", "status": "APPLIED"},
                    {"id": "mock-app-2", "candidate_name": "Jane Smith (Mock)", "email": "jane@example.com", "status": "INTERVIEWING"}
                ]

            response = requests.get(f"{self.base_url}/applications?job_id={job_id}", headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            applications = []
            for app in data:
                applications.append({
                    "id": str(app.get('id')),
                    "candidate_name": app.get('person', {}).get('name') or "Unknown",
                    "email": "Unknown", # Email is not always exposed in the basic list response
                    "status": app.get('status') or "APPLIED"
                })
            return applications

        except requests.exceptions.RequestException as e:
            print(f"Error fetching applications: {e}")
            raise e
