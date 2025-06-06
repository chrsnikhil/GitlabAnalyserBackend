# Agent Ops: AI-Powered GitLab CI/CD Pipeline Generator

Agent Ops is an intelligent platform designed to automate and optimize the process of creating and managing GitLab CI/CD pipelines. By analyzing your codebase and leveraging AI, it helps developers quickly generate efficient, secure, and best-practice-aligned pipelines.

## ✨ Features

*   **Automated Codebase Analysis:** Deeply analyzes your repository structure, dependencies, and programming languages.
*   **AI-Powered Pipeline Generation:** Generates optimized GitLab CI/CD pipeline YAML based on project analysis and prebuilt templates.
*   **Real-time Pipeline Validation:** Integrates with GitLab CI Lint API to validate generated pipelines and identify syntax errors or configuration issues.
*   **Comprehensive Code Review:** Provides AI-driven code reviews, highlighting potential issues, security vulnerabilities, and suggesting improvements.
*   **Actionable Recommendations:** Offers insights and recommendations for improving code quality, security, and pipeline performance.
*   **User-Friendly Interface:** A clean and intuitive frontend for easy interaction and visualization of results.

## 🛠️ Tech Stack

**Frontend:**
*   Next.js
*   TypeScript
*   Tailwind CSS
*   Framer Motion (for animations)
*   Recharts (for data visualization)

**Backend:**
*   FastAPI (Python)
*   OpenAI API (for AI analysis and generation)
*   GitLab API (for repository access, validation, etc.)
*   Operation Store (custom implementation for managing asynchronous task status)

## 🚀 How It Works

Agent Ops follows a workflow-based approach:

1.  **Connect Repository:** User provides a GitLab repository URL and branch.
2.  **Analysis:** The backend's `CodeAnalysisAgent` analyzes the repository's structure, languages, and dependencies by interacting with the GitLab API. Results are stored in the `OperationStore`.
3.  **Pipeline Generation:** Based on the analysis results, the `PipelineAgent` uses AI and prebuilt templates to generate an optimized `gitlab-ci.yml` file. This is stored in the `OperationStore`.
4.  **Validation:** The `ValidationAgent` sends the generated pipeline YAML to the GitLab CI Lint API for syntax and configuration validation. Results are stored.
5.  **Code Review:** The `CodeAnalysisAgent` performs an AI-powered review of key files in the repository using the OpenAI API, identifying issues and generating recommendations. Results are stored.
6.  **Results Display:** The frontend polls the `OperationStore` for the status and results of each operation, displaying the analysis, generated pipeline, validation status, and code review findings to the user.

## 🚦 Getting Started

### Prerequisites

*   Python 3.8+
*   Node.js and npm/yarn/pnpm
*   An OpenAI API key
*   Access to a GitLab instance (public or private)

### Installation

1.  **Clone the repositories:**
    ```bash
    git clone https://github.com/chrsnikhil/GitlabAnalyserFrontend.git
    git clone https://github.com/chrsnikhil/GitlabAnalyserBackend.git
    ```

2.  **Backend Setup:**
    ```bash
    cd GitlabAnalyserBackend
    pip install -r requirements.txt
    # Create a .env file and add your OpenAI API key and other necessary configurations
    # Example .env:
    # OPENAI_API_KEY=your_openai_api_key
    # GITLAB_PRIVATE_TOKEN=your_gitlab_token # Optional, for private repos
    # GITLAB_URL=https://gitlab.com # Your GitLab instance URL
    uvicorn main:app --reload
    ```

3.  **Frontend Setup:**
    ```bash
    cd ../GitlabAnalyserFrontend
    npm install # or yarn install or pnpm install
    # Create a .env.local file and set your backend URL
    # Example .env.local:
    # NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 # or your deployed backend URL
    npm run dev # or yarn dev or pnpm dev
    ```

4.  **Access the Application:**
    Open your browser to `http://localhost:3000`.

### Usage

1.  Navigate to the "Analyze" page.
2.  Enter the URL of a public GitLab repository (or a private one if you configured a GitLab token in the backend).
3.  Enter the branch name you want to analyze.
4.  Click "Start Workflow Analysis".
5.  Observe the progress and review the generated pipeline and analysis results.

## 🔗 Links

*   Frontend Repository: [https://github.com/chrsnikhil/GitlabAnalyserFrontend](https://github.com/chrsnikhil/GitlabAnalyserFrontend)
*   Backend Repository: [https://github.com/chrsnikhil/GitlabAnalyserBackend](https://github.com/chrsnikhil/GitlabAnalyserBackend)
*   Deployed Frontend: [https://gitlab-analyser-frontend.vercel.app/](https://gitlab-analyser-frontend.vercel.app/)
*   Deployed Backend: [https://gitlabanalyserbackend.onrender.com/](https://gitlabanalyserbackend.onrender.com/)
*   Demo Video: [https://www.youtube.com/watch?v=yUsPXShS3qc](https://www.youtube.com/watch?v=yUsPXShS3qc)

## 🙏 Contributing

We welcome contributions! Please see the contributing guidelines in each repository for details.

## 📫 Contact

For questions or support, please contact chrsnikhil@gmail.com.
