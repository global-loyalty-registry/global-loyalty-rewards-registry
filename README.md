# Global Loyalty & Rewards Registry

A structured reference API and validation engine for the global travel and lifestyle rewards ecosystem. Providing real-time schema validation across suppliers, including: Airlines, Hotels, Rail, Car Rental, Credit Cards, and Cruise Lines.

## 🚀 Features
- **Standardized Data:** Uniform JSON structure for disparate loyalty programs.
- **Validation Engine:** Built-in Regex patterns for member number verification (e.g., Iryo, Enterprise, National).
- **Agent-First Architecture:** Strictly typed OpenAPI 3.1 spec optimized for LLM tool-calling and autonomous agentic workflows.n.

## 🛠 Tech Stack
- **Framework:** FastAPI (Python 3.10+)
- **Deployment:** Railway.app
- **Server:** Uvicorn
- **Documentation:** Interactive Swagger UI (Available at /docs)

## 🔑 Public Beta Authentication
- **API Key:** GUESTBETA2026
- **Header Format:** Authorization: Bearer GUESTBETA2026

## 🏁 Quick Start

### ⚡ Instant Web Test (Recommended)
The fastest way to test the registry is via our interactive documentation.
1. Visit: `https://web-production-c81b0.up.railway.app/docs`
2. Click **Authorize** and enter the key: `GUESTBETA2026`
3. Try any endpoint (e.g., `/programs/search`) directly from your browser.

**AI Agents** Visit: `https://web-production-c81b0.up.railway.app/openapi.json`

### 🛠 Local Development & Contributions
If you wish to clone the registry, run it locally, or contribute to the schema:
1. **Clone**: `git clone https://github.com/global-loyalty-registry/registry-api.git`
2. **Setup**: `cp .env.example .env`
3. **Install**: `pip install -r requirements.txt`
4. **Run**: `uvicorn main:app --reload`
