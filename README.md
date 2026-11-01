# TrustFlow AI 🚀

**An AI-powered developer assistant for CI/CD failure analysis and deployment monitoring.**

TrustFlow AI helps developers investigate failed builds and GitHub Actions workflows by combining Python-based tools with Google's Gemini API. It interprets natural-language requests, retrieves relevant CI/CD information, extracts error context from logs, and generates AI-assisted explanations with suggested fixes.

> **Project Status:** In Progress 🚧

## ✨ Features

- **Natural-Language Interface:** Describe a development or CI/CD issue in plain English.
- **Failed Build Detection:** Retrieve failed builds and filter them by service.
- **Deployment Status:** Check deployment status for supported services.
- **GitHub Actions Integration:** Retrieve recent workflow runs and inspect workflow jobs.
- **Automated Failure Analysis:** Extract relevant error messages and surrounding log context.
- **AI-Powered Explanations:** Use Gemini to identify likely causes, provide supporting evidence, and suggest fixes.
- **Input Validation:** Validate interpreted requests using Pydantic before executing tools.
- **Structured Tool Routing:** Route requests to the appropriate function through a tool registry.
- **Error Handling and Logging:** Handle tool execution failures and record useful diagnostic information.
- **Automated Testing:** Use Pytest to test request handling, validation, and log-analysis behavior.
- **CI Testing:** Run automated tests through GitHub Actions.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application and tool implementation |
| Google Gemini API | Natural-language understanding and failure explanations |
| GitHub Actions API | Workflow runs, job details, and CI failure investigation |
| Pydantic | Request validation and structured data |
| Pytest | Automated testing |
| Git and GitHub | Version control and repository hosting |

## 🏗️ Project Structure

```text
TrustFlowAI/
├── app.py
├── understand_request.py
├── validation.py
├── tools/
│   ├── __init__.py
│   ├── builds.py
│   ├── github_actions.py
│   ├── log_analysis.py
│   └── workflow_analysis.py
├── tests/
│   ├── test_app.py
│   ├── test_tools.py
│   ├── test_validation.py
│   └── test_log_analysis.py
├── .github/
│   └── workflows/
├── .env                  # Local secrets; do not commit
├── .gitignore
└── README.md
```

*The tree above describes the main project components; your exact test files and workflow filenames may vary.*

## ⚙️ Getting Started

### Prerequisites

- Python 3.10 or later
- Git
- A Google Gemini API key
- A GitHub account and repository access for GitHub Actions analysis

### 1. Clone the repository

```bash
git clone https://github.com/PallaviSatram/TrustFlowAI.git
cd TrustFlowAI
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install google-genai python-dotenv pydantic pytest
```

If the project has a `requirements.txt` file, you can install the pinned dependencies with:

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_token
```

- `GEMINI_API_KEY`: Used to access the Gemini API.
- `GITHUB_TOKEN`: Used for authenticated GitHub API access if configured by the application.

Generate credentials through the official [Google AI Studio](https://aistudio.google.com/) and [GitHub token settings](https://github.com/settings/tokens).

**Security:** Never commit your `.env` file, API keys, or access tokens. Ensure `.env` and `.venv/` are included in `.gitignore`.

### 5. Run the application

```bash
python app.py
```

Enter a natural-language request when prompted.

## 💬 Example Requests

Try requests such as:

```text
List all failed builds.
```

```text
Check the deployment status of the payment service.
```

```text
Show the recent GitHub Actions workflow runs.
```

```text
Analyze the latest failed GitHub Actions workflow and explain why it failed.
```

The application interprets the request, validates the selected action, and executes the corresponding tool. For workflow analysis, it retrieves relevant job logs and uses Gemini to produce a structured explanation.

## 🧠 How It Works

```text
User Request
     |
     v
Gemini-Powered Request Interpretation
     |
     v
Pydantic Request Validation
     |
     v
Tool Registry and Request Routing
     |
     +--------------------+
     |                    |
     v                    v
Build / Deployment    GitHub Actions
Tools                 Workflow Analysis
                          |
                          v
                    Job Log Retrieval
                          |
                          v
                    Error Context Extraction
                          |
                          v
                    Gemini Failure Explanation
                          |
                          v
                    Results to the User
```

### Workflow failure analysis

1. Retrieve recent GitHub Actions workflow runs.
2. Identify the most recent completed failed workflow among the retrieved runs.
3. Fetch its job information and analyze relevant logs.
4. Extract error messages and surrounding context.
5. Ask Gemini to explain the likely cause, supporting evidence, and potential fix.
6. Present the analysis in the CLI.

AI-generated explanations are diagnostic suggestions, not guaranteed fixes. Review the supporting logs before applying a recommendation.

## 🧪 Running Tests

Run the complete test suite from the project root:

```bash
python -m pytest -q
```

For verbose output:

```bash
python -m pytest -v
```

The tests cover request validation, application behavior, tool execution, and log-analysis logic. Tests that interact with external services should use mocks where appropriate to avoid unnecessary API calls.

## 🔐 Security Considerations

- Keep API keys and tokens in environment variables.
- Never print or commit secret values.
- Validate requests before executing tools.
- Handle API errors and unexpected responses safely.
- Review AI-generated recommendations before making changes to a deployment or CI/CD pipeline.

## 🗺️ Future Improvements

- Add support for more CI/CD platforms.
- Improve failure classification and root-cause detection.
- Add historical failure tracking and recurring-error detection.
- Introduce richer diagnostic reports and an interactive dashboard.
- Expand automated tests for workflow analysis and external API failures.

## 🎯 Project Goal

The goal of TrustFlow AI is to reduce the manual effort involved in investigating failed CI/CD pipelines by making build information easier to retrieve and log errors easier to understand.

## 👩‍💻 Author

**Pallavi Satram**

- GitHub: [@PallaviSatram](https://github.com/PallaviSatram)

---

⭐ If you find this project interesting, feel free to explore the repository and follow its development.
