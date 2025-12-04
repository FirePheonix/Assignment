# gemnar-website

## Quick Setup

1. **Environment Configuration**: Copy the example environment file and configure your API keys:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your actual API keys (see [API Configuration](#api-configuration) section below).

2. **Check Configuration**: Run the configuration checker:
   ```bash
   python3 check_config.py
   ```

3. **Install Dependencies and Run**:
   ```bash
   poetry install
   poetry run python manage.py migrate
   poetry run uvicorn gemnar.asgi:application --reload --reload-dir website/templates
   ```

## API Configuration

### Required for AI Tweet Generation

To use the AI tweet generation features, you need to configure the following environment variables in your `.env` file:

#### OpenAI API (Required for AI tweet generation)
```env
OPENAI_API_KEY=your_openai_api_key_here
```
Get your API key from: https://platform.openai.com/api-keys

#### Twitter API (Required for posting tweets)
```env
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
TWITTER_USERNAME=your_twitter_username_here
```
Get your Twitter API credentials from: https://developer.twitter.com

### Troubleshooting

If you encounter "error generating ai tweet":

1. **Check your configuration**:
   ```bash
   python3 check_config.py
   ```

2. **Common issues**:
   - Missing `.env` file → Copy `.env.example` to `.env`
   - Invalid OpenAI API key → Check your key at https://platform.openai.com/api-keys
   - OpenAI quota exceeded → Check your billing at https://platform.openai.com/account/billing
   - Missing environment variables → Ensure all required variables are set in `.env`

## Database Setup

This project uses PostgreSQL in production and can use either SQLite (for development) or PostgreSQL locally.

### PostgreSQL Setup (Recommended)

1. Install PostgreSQL:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   ```

2. Create database and user:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE gemnar_db;
   CREATE USER gemnar_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE gemnar_db TO gemnar_user;
   \q
   ```

3. Set environment variables in your `.env` file:
   ```
   DB_NAME=gemnar_db
   DB_USER=gemnar_user
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

## Running locally

1. Install dependencies:
   ```bash
   poetry install
   ```
2. Run migrations:
   ```bash
   poetry run python manage.py migrate
   ```
3. Start the server:
   ```bash
   poetry run uvicorn gemnar.asgi:application --reload --reload-dir website/templates
   ```

Visit http://127.0.0.1:8000/ to see the landing page.

## Deployment

The project includes Ansible playbooks for automated deployment with PostgreSQL setup. The playbook will:

- Install and configure PostgreSQL
- Create the database and user
- Set up environment variables
- Run migrations automatically

Run deployment with:
```bash
cd ansible
./deploy.sh
```
