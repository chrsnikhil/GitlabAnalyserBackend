from typing import Any, Dict
from .base_agent import BaseAgent
import yaml

class PipelineGenAgent(BaseAgent):
    def __init__(self):
        """Initialize the PipelineGenAgent"""
        super().__init__()
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a CI/CD pipeline based on repository analysis
        
        Args:
            context: Dictionary containing:
                - analysis: Results from CodeAnalysisAgent
                - repo_url: URL of the GitLab repository
                - branch: Branch to analyze
                
        Returns:
            Dictionary containing the generated pipeline
        """
        try:
            analysis = context.get("analysis")
            if not analysis:
                raise ValueError("Repository analysis is required")
            
            # Generate pipeline using OpenAI
            pipeline_yaml = await self._generate_pipeline(analysis)
            
            # Validate YAML syntax
            try:
                yaml.safe_load(pipeline_yaml)
            except yaml.YAMLError as e:
                # If YAML is invalid, try to fix common issues
                pipeline_yaml = self._fix_common_yaml_issues(pipeline_yaml)
                try:
                    yaml.safe_load(pipeline_yaml)
                except yaml.YAMLError as e:
                    raise ValueError(f"Generated pipeline has invalid YAML syntax: {str(e)}")
            
            return {
                "status": "success",
                "message": "Pipeline generated successfully",
                "data": {
                    "pipeline_yaml": pipeline_yaml
                }
            }
            
        except Exception as e:
            return self._format_error(e)
    
    async def _generate_pipeline(self, analysis: Dict[str, Any]) -> str:
        """Generate pipeline using OpenAI with optimized prompt"""
        # Extract key information from analysis
        language = analysis.get("language", "unknown")
        has_docker = analysis.get("has_dockerfile", False)
        has_tests = analysis.get("has_tests", False)
        build_steps = analysis.get("build_steps", [])
        test_steps = analysis.get("test_steps", [])
        deploy_steps = analysis.get("deploy_steps", [])
        
        # Create a detailed prompt for pipeline generation
        prompt = f"""Create a GitLab CI/CD pipeline for a {language} project with the following requirements:

Project Details:
- Language: {language}
- Has Dockerfile: {has_docker}
- Has Tests: {has_tests}

Required Stages:
1. Build Stage:
   - Steps: {', '.join(build_steps)}
   - Use appropriate {language} base image
   - Cache dependencies
   - Build artifacts

2. Test Stage:
   - Steps: {', '.join(test_steps) if test_steps else 'No test steps specified'}
   - Run tests if present
   - Generate test reports

3. Deploy Stage:
   - Steps: {', '.join(deploy_steps)}
   - Deploy to production
   - Include deployment verification

Additional Requirements:
- Use GitLab CI/CD best practices
- Include proper caching
- Add appropriate environment variables
- Include job dependencies
- Add proper artifacts handling
- Include deployment conditions

Return only the YAML configuration without any explanations or markdown formatting."""
        
        pipeline = await self._call_openai(prompt)
        
        # Clean up the response to ensure it's valid YAML
        pipeline = self._clean_yaml_response(pipeline)
        return pipeline
    
    def _clean_yaml_response(self, yaml_str: str) -> str:
        """Clean up YAML response from OpenAI"""
        yaml_str = yaml_str.strip()
        
        # Remove markdown code blocks if present
        if yaml_str.startswith("```yaml"):
            yaml_str = yaml_str[7:]
        if yaml_str.startswith("```"):
            yaml_str = yaml_str[3:]
        if yaml_str.endswith("```"):
            yaml_str = yaml_str[:-3]
            
        return yaml_str.strip()
    
    def _fix_common_yaml_issues(self, yaml_str: str) -> str:
        """Fix common YAML syntax issues"""
        # Remove any non-YAML text
        lines = yaml_str.split('\n')
        yaml_lines = []
        in_yaml = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_yaml = not in_yaml
                continue
            if in_yaml or not line.strip().startswith('```'):
                yaml_lines.append(line)
        
        return '\n'.join(yaml_lines) 