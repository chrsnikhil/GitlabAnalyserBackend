from typing import Dict, Any
from .base_agent import BaseAgent

class PipelineAgent(BaseAgent):
    def __init__(self):
        """Initialize the PipelineAgent"""
        super().__init__()
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a GitLab CI pipeline based on repository analysis
        
        Args:
            context: Dictionary containing:
                - analysis: Repository analysis results
                - repo_url: URL of the GitLab repository
                - branch: Branch to analyze
                
        Returns:
            Dictionary containing pipeline generation results
        """
        try:
            analysis = context.get("analysis", {})
            if not analysis:
                raise ValueError("Repository analysis is required")
            
            # Generate basic pipeline
            pipeline_yaml = self._generate_basic_pipeline(analysis)
            
            return self._format_success(
                "Pipeline generation completed",
                {"pipeline_yaml": pipeline_yaml}
            )
            
        except Exception as e:
            return self._format_error(e)
    
    def _generate_basic_pipeline(self, analysis: Dict[str, Any]) -> str:
        """Generate a basic GitLab CI pipeline"""
        stages = ["build", "test", "deploy"]
        language = analysis.get("language", "unknown")
        
        # Basic pipeline template
        pipeline = f"""
stages:
  - build
  - test
  - deploy

variables:
  DOCKER_DRIVER: overlay2

build:
  stage: build
  image: {self._get_language_image(language)}
  script:
    - echo "Building application..."
    - {self._get_build_commands(language)}
  artifacts:
    paths:
      - build/
    expire_in: 1 week

test:
  stage: test
  image: {self._get_language_image(language)}
  script:
    - echo "Running tests..."
    - {self._get_test_commands(language)}
  dependencies:
    - build

deploy:
  stage: deploy
  image: alpine:latest
  script:
    - echo "Deploying application..."
    - echo "Deployment completed successfully"
  only:
    - main
"""
        return pipeline
    
    def _get_language_image(self, language: str) -> str:
        """Get the appropriate Docker image for the language"""
        images = {
            "python": "python:3.9",
            "javascript": "node:16",
            "typescript": "node:16",
            "java": "maven:3.8",
            "ruby": "ruby:3.0",
            "php": "php:8.0",
            "go": "golang:1.16"
        }
        return images.get(language, "alpine:latest")
    
    def _get_build_commands(self, language: str) -> str:
        """Get build commands for the language"""
        commands = {
            "python": "pip install -r requirements.txt && python setup.py build",
            "javascript": "npm install && npm run build",
            "typescript": "npm install && npm run build",
            "java": "mvn clean package",
            "ruby": "bundle install && bundle exec rake build",
            "php": "composer install && php artisan build",
            "go": "go build -o app"
        }
        return commands.get(language, "echo 'No build commands defined'")
    
    def _get_test_commands(self, language: str) -> str:
        """Get test commands for the language"""
        commands = {
            "python": "python -m pytest",
            "javascript": "npm test",
            "typescript": "npm test",
            "java": "mvn test",
            "ruby": "bundle exec rspec",
            "php": "php artisan test",
            "go": "go test ./..."
        }
        return commands.get(language, "echo 'No test commands defined'") 