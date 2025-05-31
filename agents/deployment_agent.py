from typing import Any, Dict
import gitlab
from .base_agent import BaseAgent
import os
from google.cloud import run_v2, artifactregistry_v1
from google.cloud.run_v2 import Service

class DeploymentAgent(BaseAgent):
    def __init__(self):
        """Initialize the DeploymentAgent with GitLab and Google Cloud configuration"""
        super().__init__()
        self.gitlab_url = os.getenv("GITLAB_URL")
        self.gitlab_token = os.getenv("GITLAB_TOKEN")
        self.project_id = os.getenv("GOOGLE_PROJECT_ID")
        
        if not self.gitlab_url or not self.gitlab_token:
            raise ValueError("GitLab configuration is missing")
        if not self.project_id:
            raise ValueError("Google Cloud project ID is missing")
            
        self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_token)
        self.run_client = run_v2.ServicesClient()
        self.artifact_client = artifactregistry_v1.ArtifactRegistryClient()
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy the validated pipeline and optionally set up Google Cloud resources
        
        Args:
            context: Dictionary containing:
                - pipeline_yaml: The validated pipeline YAML
                - repo_url: URL of the GitLab repository
                - deploy_to_cloud: Whether to deploy to Google Cloud
                
        Returns:
            Dictionary containing deployment results
        """
        try:
            pipeline_yaml = context.get("pipeline_yaml")
            repo_url = context.get("repo_url")
            deploy_to_cloud = context.get("deploy_to_cloud", False)
            
            if not pipeline_yaml:
                raise ValueError("Pipeline YAML is required")
            
            # Get project
            project_path = self._extract_project_path(repo_url)
            project = self.gl.projects.get(project_path)
            
            # Deploy pipeline to GitLab
            pipeline_result = await self._deploy_pipeline(project, pipeline_yaml)
            
            # Set up Google Cloud if requested
            cloud_result = None
            if deploy_to_cloud:
                cloud_result = await self._setup_cloud_resources(project)
            
            return {
                "status": "success",
                "message": "Deployment completed successfully",
                "data": {
                    "pipeline": pipeline_result,
                    "cloud": cloud_result
                }
            }
            
        except Exception as e:
            return self._format_error(e)
    
    def _extract_project_path(self, repo_url: str) -> str:
        """Extract project path from GitLab URL"""
        path = repo_url.split("//")[-1].split("/")[1:]
        return "/".join(path)
    
    async def _deploy_pipeline(self, project: Any, pipeline_yaml: str) -> Dict[str, Any]:
        """Deploy pipeline to GitLab repository"""
        try:
            # Create or update .gitlab-ci.yml
            try:
                file = project.files.get(".gitlab-ci.yml", "main")
                file.content = pipeline_yaml
                file.save(branch="main", commit_message="Update CI/CD pipeline")
            except:
                project.files.create({
                    'file_path': '.gitlab-ci.yml',
                    'branch': 'main',
                    'content': pipeline_yaml,
                    'commit_message': 'Add CI/CD pipeline'
                })
            
            return {
                "status": "success",
                "message": "Pipeline deployed to GitLab",
                "pipeline_url": f"{project.web_url}/-/pipelines"
            }
        except Exception as e:
            raise Exception(f"Error deploying pipeline: {str(e)}")
    
    async def _setup_cloud_resources(self, project: Any) -> Dict[str, Any]:
        """Set up Google Cloud resources"""
        try:
            # Create Artifact Registry repository
            repo_name = f"projects/{self.project_id}/locations/us-central1/repositories/{project.path}"
            try:
                repo = self.artifact_client.get_repository(name=repo_name)
            except:
                repo = self.artifact_client.create_repository(
                    parent=f"projects/{self.project_id}/locations/us-central1",
                    repository_id=project.path,
                    repository=artifactregistry_v1.Repository(
                        format_=artifactregistry_v1.Repository.Format.DOCKER
                    )
                )
            
            # Create Cloud Run service
            service_name = f"projects/{self.project_id}/locations/us-central1/services/{project.path}"
            try:
                service = self.run_client.get_service(name=service_name)
            except:
                service = Service(
                    template=Service.Template(
                        containers=[
                            Service.Template.Container(
                                image=f"us-central1-docker.pkg.dev/{self.project_id}/{project.path}/app:latest",
                                ports=[Service.Template.Container.Port(container_port=8080)],
                                resources=Service.Template.Container.Resources(
                                    limits={"cpu": "1", "memory": "512Mi"}
                                )
                            )
                        ]
                    )
                )
                service = self.run_client.create_service(
                    parent=f"projects/{self.project_id}/locations/us-central1",
                    service_id=project.path,
                    service=service
                )
            
            return {
                "status": "success",
                "message": "Google Cloud resources created",
                "artifact_registry": repo.name,
                "cloud_run": service.name
            }
        except Exception as e:
            raise Exception(f"Error setting up Google Cloud resources: {str(e)}") 