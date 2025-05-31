from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
from agents.code_analysis_agent import CodeAnalysisAgent
from agents.pipeline_agent import PipelineAgent
from agents.validation_agent import ValidationAgent
from agents.deployment_agent import DeploymentAgent
from datetime import datetime
import json
from operation_store import get_operation, set_operation

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Pipeline Generator",
    description="An AI-powered platform for generating and deploying CI/CD pipelines",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gitlab-workflow-frontend.onrender.com",  # Render frontend URL
        "http://localhost:3000",  # Local development
        "https://gitlab-workflow-backend.onrender.com",  # Render backend URL
        "https://gitlab-analyser-frontend.vercel.app" # Vercel frontend URL (removed trailing slash)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class RepositoryAnalysis(BaseModel):
    repo_url: HttpUrl
    branch: Optional[str] = "main"
    language: Optional[str] = None
    deploy_to_cloud: Optional[bool] = False

class PipelineResponse(BaseModel):
    status: str
    message: str
    operation_id: Optional[str] = None
    pipeline_yaml: Optional[str] = None
    validation_status: Optional[bool] = None
    suggestions: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None

class CodeReviewRequest(BaseModel):
    repo_url: HttpUrl
    branch: Optional[str] = "main"
    focus_areas: Optional[List[str]] = ["security", "performance", "best_practices"]

class CodeReviewResponse(BaseModel):
    review_id: str
    status: str
    message: str
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    score: float

class ValidationRequest(BaseModel):
    pipeline_yaml: str
    repo_url: HttpUrl

# Routes
@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Pipeline Generator API",
        "version": "1.0.0",
        "endpoints": [
            "/analyze",
            "/generate-pipeline",
            "/validate",
            "/deploy",
            "/code-review",
            "/status/{operation_id}"
        ]
    }

@app.post("/analyze", response_model=Dict[str, Any])
async def analyze_repository(repo: RepositoryAnalysis, background_tasks: BackgroundTasks):
    """
    Analyze a GitLab repository to understand its structure and requirements
    """
    try:
        operation_id = f"analyze_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        agent = CodeAnalysisAgent()
        
        # Start analysis in background
        async def run_analysis():
            result = await agent.execute({
                "repo_url": str(repo.repo_url),
                "branch": repo.branch
            })
            set_operation(operation_id, result)
        
        background_tasks.add_task(run_analysis)
        
        return {
            "status": "processing",
            "message": "Repository analysis started",
            "operation_id": operation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-pipeline", response_model=PipelineResponse)
async def generate_pipeline(repo: RepositoryAnalysis, background_tasks: BackgroundTasks):
    """
    Generate a CI/CD pipeline based on repository analysis
    """
    try:
        operation_id = f"generate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # First analyze the repository
        analysis_agent = CodeAnalysisAgent()
        analysis_result = await analysis_agent.execute({
            "repo_url": str(repo.repo_url),
            "branch": repo.branch
        })
        
        if analysis_result["status"] == "error":
            raise HTTPException(status_code=500, detail=analysis_result["message"])
        
        # Generate pipeline
        pipeline_agent = PipelineAgent()
        async def run_generation():
            result = await pipeline_agent.execute({
                "analysis": analysis_result["data"],
                "repo_url": str(repo.repo_url),
                "branch": repo.branch
            })
            set_operation(operation_id, result)
        
        background_tasks.add_task(run_generation)
        
        return PipelineResponse(
            status="processing",
            message="Pipeline generation started",
            operation_id=operation_id,
            data=analysis_result["data"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate")
async def validate_pipeline(request: ValidationRequest, background_tasks: BackgroundTasks):
    """
    Validate the generated pipeline using GitLab CI Lint API
    """
    try:
        operation_id = f"validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        agent = ValidationAgent()
        
        async def run_validation():
            result = await agent.execute({
                "pipeline_yaml": request.pipeline_yaml,
                "repo_url": str(request.repo_url)
            })
            set_operation(operation_id, result)
        
        background_tasks.add_task(run_validation)
        
        return {
            "status": "processing",
            "message": "Pipeline validation started",
            "operation_id": operation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deploy")
async def deploy_pipeline(repo: RepositoryAnalysis, pipeline_yaml: str, background_tasks: BackgroundTasks):
    """
    Deploy the validated pipeline to GitLab
    """
    try:
        operation_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        agent = DeploymentAgent()
        
        async def run_deployment():
            result = await agent.execute({
                "pipeline_yaml": pipeline_yaml,
                "repo_url": str(repo.repo_url),
                "deploy_to_cloud": repo.deploy_to_cloud
            })
            set_operation(operation_id, result)
        
        background_tasks.add_task(run_deployment)
        
        return {
            "status": "processing",
            "message": "Pipeline deployment started",
            "operation_id": operation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{operation_id}")
async def get_operation_status(operation_id: str):
    """
    Get the status of an async operation
    """
    op = get_operation(operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op

@app.post("/code-review", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest, background_tasks: BackgroundTasks):
    """
    Perform a code review using OpenAI
    """
    try:
        operation_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        async def run_review():
            # Perform analysis to get repo details
            analysis_agent = CodeAnalysisAgent()
            analysis_result = await analysis_agent.execute({
                "repo_url": str(request.repo_url),
                "branch": request.branch
            })
            
            if analysis_result["status"] == "error":
                set_operation(operation_id, {
                    "review_id": operation_id,
                    "status": "error",
                    "message": analysis_result["message"],
                    "findings": [],
                    "recommendations": [],
                    "score": 0
                })
                return

            # Get repository content for review
            project_path = analysis_agent._extract_project_path(str(request.repo_url))
            project = analysis_agent.gl.projects.get(project_path)
            
            # Get main code files
            files = project.repository_tree(ref=request.branch, recursive=True)
            code_files = [f for f in files if f["type"] == "blob" and not f["path"].startswith((".git", "node_modules", "__pycache__"))]
            print(f"[DEBUG] Found {len(code_files)} code files to review: {[f['path'] for f in code_files]}")
            if not code_files:
                print("[DEBUG] No code files found for review.")
            
            # Review each file
            findings = []
            recommendations = []
            total_score = 0
            files_reviewed = 0
            openai_failed = False
            openai_error_message = None
            
            try:
                for file in code_files[:5]:  # Limit to first 5 files to avoid rate limits
                    try:
                        content = project.files.get(file["path"], request.branch).decode().decode()
                        
                        # Create review prompt with explicit JSON instructions
                        prompt = f"""Review this code file ({file['path']}) for:
1. Code quality and best practices
2. Potential bugs or issues
3. Security concerns
4. Performance improvements
5. Maintainability

Focus areas: {', '.join(request.focus_areas)}

Provide the review strictly as a valid JSON object with the following keys: "findings" (list of strings), "recommendations" (list of strings), and "score" (number between 0 and 10).

Code:
{content[:2000]}  # Limit content length
"""
                        
                        # Get review from OpenAI
                        try:
                            review = await analysis_agent._call_openai(prompt)
                            print(f"[DEBUG] OpenAI review response for {file['path']}: {review}")
                            
                            try:
                                # Attempt to parse the review as JSON
                                review_data = json.loads(review)
                                findings.extend(review_data.get("findings", []))
                                recommendations.extend(review_data.get("recommendations", []))
                                total_score += review_data.get("score", 0)
                                files_reviewed += 1
                            except json.JSONDecodeError as json_e:
                                # Handle JSON parsing errors gracefully
                                print(f"[ERROR] JSON parsing failed for {file['path']}: {json_e}")
                                print(f"[ERROR] Malformed JSON response: {review}")
                                findings.append({
                                    "type": "error",
                                    "severity": "low",
                                    "description": f"Failed to parse review for {file['path']} due to invalid JSON response from AI.",
                                    "location": file["path"]
                                })
                                # Do NOT break here, continue with other files

                        except Exception as oe:
                            # Handle other OpenAI call errors (like quota exceeded)
                            openai_failed = True
                            openai_error_message = str(oe)
                            print(f"[ERROR] OpenAI failed for {file['path']}: {oe}")
                            break  # Stop further OpenAI calls if one fails
                    except Exception as e:
                        findings.append({
                            "type": "error",
                            "severity": "medium",
                            "description": f"Error reviewing {file['path']}: {str(e)}",
                            "location": file["path"]
                        })
                print(f"[DEBUG] Finished reviewing files. Files reviewed: {files_reviewed}")
            except Exception as e:
                openai_failed = True
                openai_error_message = str(e)
                print(f"[ERROR] Unexpected error in code review: {e}")
            
            # Fallback to mock review if OpenAI failed or no files reviewed
            if openai_failed or files_reviewed == 0:
                findings = [
                    {
                        "type": "mock_review",
                        "severity": "info",
                        "description": "OpenAI review failed or quota exceeded. This is a mock code review.",
                        "location": "N/A"
                    }
                ]
                recommendations = [
                    "Add more tests to your codebase.",
                    "Follow best practices for code structure.",
                    "Ensure proper error handling."
                ]
                score = 50
                summary = f"OpenAI review failed: {openai_error_message or 'Unknown error'}. Returned mock review."
            else:
                score = total_score / files_reviewed if files_reviewed > 0 else 0
                # Get overall recommendations
                if findings or recommendations:
                    summary_prompt = f"""Based on these findings and recommendations, provide a summary of the most important improvements needed:\nFindings: {json.dumps(findings)}\nRecommendations: {json.dumps(recommendations)}\n\nReturn a brief summary paragraph."""
                    try:
                        summary = await analysis_agent._call_openai(summary_prompt)
                    except Exception as oe:
                        summary = f"OpenAI summary failed: {oe}."
                else:
                    summary = "No significant issues found in the reviewed files."
            set_operation(operation_id, {
                "review_id": operation_id,
                "status": "completed",
                "message": "Code review completed" if not openai_failed else "Code review completed with mock fallback due to OpenAI error.",
                "findings": findings,
                "recommendations": recommendations,
                "score": score,
                "summary": summary
            })
        
        background_tasks.add_task(run_review)
        
        return CodeReviewResponse(
            review_id=operation_id,
            status="processing",
            message="Code review started",
            findings=[], 
            recommendations=[],
            score=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 