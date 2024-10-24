# Data Fusion Catalog Manager

A comprehensive catalog management system with AI-powered product enrichment capabilities.

## Features

- Product catalog management
- AI-powered product enrichment (OpenAI/Gemini)
- Price management and competitor analysis
- Multi-language support
- FTP integration
- Sync scheduling
- User management

## Deployment Instructions

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd DataFusionCatalogManager
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run main.py
```

### Streamlit Cloud Deployment

1. Push your code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Click "New app"
4. Select your repository and branch
5. Set the main file path as `main.py`
6. Add your secrets in the Streamlit Cloud dashboard:
   - Navigate to App Settings > Secrets
   - Add the following secrets:
     ```toml
     [secrets]
     DATABASE_URL = "your_database_url"
     OPENAI_API_KEY = "your_openai_api_key"
     GEMINI_API_KEY = "your_gemini_api_key"
     ```

## Environment Variables

Create a `.streamlit/secrets.toml` file for local development:

```toml
[secrets]
DATABASE_URL = "your_database_url"
OPENAI_API_KEY = "your_openai_api_key"
GEMINI_API_KEY = "your_gemini_api_key"
```

## Database Setup

1. Create a PostgreSQL database
2. Update the DATABASE_URL in your secrets.toml
3. The application will automatically create the required tables on first run

## Security Notes

- Never commit secrets.toml or any files containing API keys
- Use environment variables for sensitive data
- Regularly rotate API keys and credentials
- Keep dependencies updated

## Support

For support, please open an issue in the GitHub repository.
