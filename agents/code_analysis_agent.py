from typing import Any, Dict, List
import gitlab
from .base_agent import BaseAgent
import os

class CodeAnalysisAgent(BaseAgent):
    def __init__(self):
        """Initialize the CodeAnalysisAgent with GitLab configuration"""
        super().__init__()
        self.gitlab_url = os.getenv("GITLAB_URL")
        self.gitlab_token = os.getenv("GITLAB_TOKEN")
        
        if not self.gitlab_url or not self.gitlab_token:
            raise ValueError("GitLab configuration is missing")
            
        self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_token)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a GitLab repository to understand its structure and requirements
        
        Args:
            context: Dictionary containing:
                - repo_url: URL of the GitLab repository
                - branch: Branch to analyze (default: main)
                
        Returns:
            Dictionary containing analysis results
        """
        try:
            repo_url = context.get("repo_url")
            branch = context.get("branch", "main")
            
            if not repo_url:
                raise ValueError("Repository URL is required")
            
            print(f"[CodeAnalysisAgent] Starting analysis for repo: {repo_url}, branch: {branch}")
            print(f"[CodeAnalysisAgent] Using GitLab URL: {self.gitlab_url}")
            
            # Extract project path from URL
            project_path = self._extract_project_path(repo_url)
            
            # Get project
            print(f"[CodeAnalysisAgent] Attempting to get project from GitLab...")
            try:
                project = self.gl.projects.get(project_path)
                print(f"[CodeAnalysisAgent] Successfully retrieved project")
            except gitlab.exceptions.GitlabGetError as e:
                if e.response_code == 404:
                    raise ValueError(f"Repository not found: {repo_url}. Please check if the URL is correct and you have access to it.")
                else:
                    raise ValueError(f"GitLab API error: {str(e)}")
            
            # Get repository structure
            print(f"[CodeAnalysisAgent] Analyzing repository structure...")
            repo_structure = await self._analyze_repo_structure(project, branch)
            print(f"[CodeAnalysisAgent] Repository structure analysis complete")
            
            # Analyze dependencies
            print(f"[CodeAnalysisAgent] Analyzing dependencies...")
            dependencies = await self._analyze_dependencies(project, branch)
            print(f"[CodeAnalysisAgent] Dependencies analysis complete")
            
            # Generate analysis
            print(f"[CodeAnalysisAgent] Generating final analysis...")
            analysis = self._generate_analysis(repo_structure, dependencies)
            print(f"[CodeAnalysisAgent] Analysis generation complete")
            
            return self._format_success(
                "Repository analysis completed",
                {
                    "structure": repo_structure,
                    "dependencies": dependencies,
                    "analysis": analysis
                }
            )
            
        except Exception as e:
            print(f"[CodeAnalysisAgent] Error during analysis: {str(e)}")
            return self._format_error(e)
    
    def _extract_project_path(self, repo_url: str) -> str:
        """Extract project path from GitLab URL, removing .git suffix if present"""
        try:
            # Remove protocol and domain
            path_parts = repo_url.split("//")[-1].split("/")
            
            # Validate URL format
            if len(path_parts) < 2:
                raise ValueError(f"Invalid GitLab URL format: {repo_url}")
            
            # Remove empty parts and get the path
            path_parts = [p for p in path_parts[1:] if p]
            
            # Join parts to get the initial path
            project_path = "/".join(path_parts)
            
            # Remove .git suffix if it exists
            if project_path.endswith(".git"):
                project_path = project_path[:-4]
            
            print(f"[CodeAnalysisAgent] Extracted project path: {project_path}")
            return project_path
            
        except Exception as e:
            raise ValueError(f"Error parsing GitLab URL: {str(e)}")
    
    async def _analyze_repo_structure(self, project: Any, branch: str) -> Dict[str, Any]:
        """Analyze repository structure"""
        try:
            items = project.repository_tree(ref=branch, recursive=True)
            return {
                "files": [item["path"] for item in items],
                "directories": [item["path"] for item in items if item["type"] == "tree"]
            }
        except Exception as e:
            raise Exception(f"Error analyzing repository structure: {str(e)}")
    
    async def _analyze_dependencies(self, project: Any, branch: str) -> Dict[str, List[str]]:
        """Analyze project dependencies"""
        try:
            # Look for common dependency files
            dependency_files = {
                "python": ["requirements.txt", "setup.py", "Pipfile"],
                "node": ["package.json"],
                "java": ["pom.xml", "build.gradle"],
                "ruby": ["Gemfile"],
                "php": ["composer.json"]
            }
            
            dependencies = {}
            for lang, files in dependency_files.items():
                for file in files:
                    try:
                        content = project.files.get(file, branch).decode().decode()
                        dependencies[lang] = content
                        break
                    except:
                        continue
            
            return dependencies
        except Exception as e:
            raise Exception(f"Error analyzing dependencies: {str(e)}")
    
    def _generate_analysis(self, structure: Dict[str, Any], dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate analysis based on repository structure and dependencies"""
        # Detect language
        language = self._detect_language(structure, dependencies)
        
        # Check for Dockerfile
        has_dockerfile = "Dockerfile" in structure["files"]
        
        # Check for tests
        has_tests = any("test" in f.lower() for f in structure["files"])
        
        # Generate build steps based on language
        build_steps = self._get_build_steps(language)
        
        # Generate test steps
        test_steps = ["run tests"] if has_tests else []
        
        # Generate deploy steps
        deploy_steps = ["deploy to Cloud Run"]
        
        return {
            "language": language,
            "has_dockerfile": has_dockerfile,
            "has_tests": has_tests,
            "build_steps": build_steps,
            "test_steps": test_steps,
            "deploy_steps": deploy_steps
        }
    
    def _detect_language(self, structure: Dict[str, Any], dependencies: Dict[str, List[str]]) -> str:
        """Detect the main programming language"""
        # Check dependencies first
        if dependencies:
            return list(dependencies.keys())[0]
        
        # Check file extensions
        extensions = {}
        for file in structure["files"]:
            ext = file.split(".")[-1].lower()
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Map extensions to languages
        ext_to_lang = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "java": "java",
            "rb": "ruby",
            "php": "php",
            "go": "go"
        }
        
        # Find most common extension
        if extensions:
            most_common = max(extensions.items(), key=lambda x: x[1])[0]
            return ext_to_lang.get(most_common, "unknown")
        
        return "unknown"
    
    def _get_build_steps(self, language: str) -> List[str]:
        """Get build steps based on language"""
        steps = {
            "python": ["install dependencies", "build wheel"],
            "javascript": ["install dependencies", "build assets"],
            "typescript": ["install dependencies", "compile typescript", "build assets"],
            "java": ["install dependencies", "compile", "package"],
            "ruby": ["install dependencies", "build gem"],
            "php": ["install dependencies", "build"],
            "go": ["install dependencies", "build binary"]
        }
        return steps.get(language, ["install dependencies", "build"]) 