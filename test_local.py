import requests
import json
import time
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = {
        "GITLAB_URL": "GitLab instance URL",
        "GITLAB_TOKEN": "GitLab access token"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        else:
            # Print first 4 characters of the key for verification
            print(f"Found {var}: {value[:4]}...")
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in your .env file")
        exit(1)
    
    # Verify the .env file location
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    print(f"\nLooking for .env file at: {env_path}")
    if os.path.exists(env_path):
        print("Found .env file")
    else:
        print("Warning: .env file not found in expected location")

def print_response(title: str, response: requests.Response):
    """Print a formatted response"""
    print(f"\n{title}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_analyze_repository() -> Dict[str, Any]:
    """Test repository analysis"""
    print("\nTesting repository analysis...")
    
    # Using a known public GitLab repository for testing
    data = {
        "repo_url": "https://gitlab.com/gitlab-org/gitlab-runner",
        "branch": "main"
    }
    
    response = requests.post(
        "http://localhost:8000/analyze",
        json=data
    )
    
    print_response("Analysis Response", response)
    
    if response.status_code == 200:
        return response.json()
    return None

def test_generate_pipeline(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Test pipeline generation"""
    print("\nTesting pipeline generation...")
    data = {
        "analysis": analysis,
        "repo_url": "https://gitlab.com/gitlab-org/gitlab-runner",
        "branch": "main"
    }
    response = requests.post(
        "http://localhost:8000/generate-pipeline",
        json=data
    )
    print_response("Pipeline Generation Response", response)
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "processing":
            operation_id = result.get("operation_id")
            print("Waiting for pipeline generation to complete...")
            time.sleep(2)  # Short wait for background task
            while True:
                status = check_operation_status(operation_id)
                if not status or status.get("detail") == "Operation not found":
                    print("Operation not found. The server may have restarted or operation tracking is not persistent.")
                    return None
                if status.get("status") != "processing":
                    return status
                time.sleep(2)  # Short polling interval
        return result
    return None

def test_validate_pipeline(pipeline: Dict[str, Any], repo_url: str) -> Dict[str, Any]:
    """Test pipeline validation"""
    print("\nTesting pipeline validation...")
    
    if not pipeline or pipeline.get("status") != "success":
        print("Skipping pipeline validation due to previous error or incomplete result.")
        return None
        
    data = {
        "pipeline_yaml": pipeline.get("data", {}).get("pipeline_yaml", ""),
        "repo_url": repo_url # Use the provided repo_url
    }
    
    response = requests.post(
        "http://localhost:8000/validate",
        json=data
    )
    
    print_response("Validation Response", response)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "processing":
            operation_id = result.get("operation_id")
            print("Waiting for pipeline validation to complete...")
            start_time = time.time()
            while time.time() - start_time < 60: # Timeout after 60 seconds
                status = check_operation_status(operation_id)
                if not status or status.get("detail") == "Operation not found":
                    print("Validation operation not found.")
                    return None
                if status.get("status") != "processing":
                    print(f"Validation completed with status: {status.get('status')}")
                    return status # Return the final status including data
                time.sleep(5) # Wait 5 seconds before polling again
            print("Pipeline validation timed out.")
            return None
        else:
            print(f"Validation completed with status: {result.get('status')}")
            return result
    return None

def test_code_review(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Test code review"""
    print("\nTesting code review...")
    
    if not analysis or analysis.get("status") != "success":
        print("Skipping code review due to previous error or incomplete result.")
        return None
        
    data = {
        "repo_url": "https://gitlab.com/gitlab-org/gitlab-runner",
        "branch": "main",
        "focus_areas": ["security", "performance", "best_practices"]
    }
    
    response = requests.post(
        "http://localhost:8000/code-review",
        json=data
    )
    
    print_response("Code Review Response", response)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "processing":
            operation_id = result.get("review_id") # Code review uses review_id
            print("Waiting for code review to complete...")
            start_time = time.time()
            while time.time() - start_time < 60: # Timeout after 60 seconds
                status = check_operation_status(operation_id)
                if not status or status.get("detail") == "Operation not found":
                    print("Code review operation not found.")
                    return None
                if status.get("status") != "processing":
                    print(f"Code review completed with status: {status.get('status')}")
                    return status # Return the final status including data
                time.sleep(5) # Wait 5 seconds before polling again
            print("Code review timed out.")
            return None
        else:
            print(f"Code review completed with status: {result.get('status')}")
            return result
    return None

def check_operation_status(operation_id: str) -> Dict[str, Any]:
    """Check the status of an operation"""
    print(f"\nChecking status for operation {operation_id}...")
    
    response = requests.get(
        f"http://localhost:8000/status/{operation_id}"
    )
    
    print_response("Status Response", response)
    return response.json() if response.status_code == 200 else None

def main():
    """Run all tests"""
    print("Starting local tests...")
    
    # Validate environment variables
    validate_environment()
    
    # Test repository analysis
    analyze_result = test_analyze_repository()
    if not analyze_result:
        print("Repository analysis failed")
        return
    
    # If analysis is processing, wait for it to complete
    if analyze_result.get("status") == "processing":
        operation_id = analyze_result.get("operation_id")
        print("Waiting for analysis to complete...")
        time.sleep(2)  # Short wait for background task
        while True:
            status = check_operation_status(operation_id)
            if not status or status.get("detail") == "Operation not found":
                print("Operation not found. The server may have restarted or operation tracking is not persistent.")
                return
            if status.get("status") != "processing":
                analyze_result = status
                break
            time.sleep(2)  # Short polling interval
    
    # Test pipeline generation
    pipeline_result = test_generate_pipeline(analyze_result)
    if not pipeline_result:
        print("Pipeline generation failed")
        return
    
    # Test pipeline validation
    # Pass the original repo_url from the analysis result
    original_repo_url = analyze_result.get("data", {}).get("repo_url") # Assuming repo_url is stored in data
    if not original_repo_url:
         print("Could not get original repo URL from analysis result.")
         return
    validation_result = test_validate_pipeline(pipeline_result, original_repo_url)
    if not validation_result:
        print("Pipeline validation failed")
        return
    
    # Test code review
    review_result = test_code_review(analyze_result)
    if not review_result:
        print("Code review failed")
        return
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 