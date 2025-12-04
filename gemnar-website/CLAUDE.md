# Gemnar Website Development Guide

## Project Setup

### Python Environment
This project uses **Poetry** for dependency management and **virtual environments**.

#### Prerequisites
- Python 3.11+
- Poetry installed (`curl -sSL https://install.python-poetry.org | python3 -`)

#### Installation
```bash
# Clone the repository
git clone <repository-url>
cd gemnar-website

# Install dependencies and create virtual environment
poetry install

# Activate the virtual environment
poetry shell

# Or run commands without activating
poetry run python manage.py runserver
```

#### Development Commands
```bash
# Run development server
poetry run python manage.py runserver

# Run development server with uvicorn (alternative ASGI server)
poetry run uvicorn gemnar.asgi:application --reload

# Run database migrations
poetry run python manage.py migrate

# Create new migrations
poetry run python manage.py makemigrations

# Run tests
poetry run python manage.py test

# Linting and formatting
poetry run ruff check .
poetry run ruff format .
```

## Architecture

### Task Processing
**We do NOT use Celery.** Instead, we use a simple cron-based approach:

- A cron job runs every minute executing: `poetry run python manage.py process_scheduled_tweets`
- This management command handles all background tasks including:
  - Posting scheduled tweets
  - Refreshing Twitter metrics
  - Processing any queued operations

#### Cron Setup
```bash
# Add to crontab (crontab -e)
* * * * * cd /path/to/gemnar-website && poetry run python manage.py send_brand_tweets >> /var/log/gemnar_cron.log 2>&1
```

### Key Management Commands
- `send_brand_tweets` - Main background processor (posts scheduled tweets, handles BrandTweet objects)
- `send_brand_instagram_posts` - Process Instagram posts
- `setup_twitter_auth` - Configure Twitter API credentials
- Various fix/maintenance commands

## Development Guidelines

### Adding New Features
1. Create database migrations: `poetry run python manage.py makemigrations`
2. Apply migrations: `poetry run python manage.py migrate`
3. Test locally with: `poetry run python manage.py runserver`

### Testing
```bash
# Run all tests
poetry run python manage.py test

# Run specific app tests
poetry run python manage.py test website

# Run with coverage
poetry run coverage run manage.py test
poetry run coverage report
```

### Database
- Uses Django ORM with PostgreSQL in production
- SQLite for local development (configured in settings)

## Deployment

### Environment Variables
Create a `.env` file with:
```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://...
OPENAI_API_KEY=your-openai-key
TWITTER_API_KEY=your-twitter-key
# ... other required variables
```

### Production Setup
1. Install dependencies: `poetry install --no-dev`
2. Collect static files: `poetry run python manage.py collectstatic`
3. Run migrations: `poetry run python manage.py migrate`
4. Set up cron job for background processing
5. Configure web server (nginx/apache) to serve the application
6. For production ASGI deployment, use: `poetry run uvicorn gemnar.asgi:application --host 0.0.0.0 --port 8000`

## Common Tasks

### Adding Tweet Strategies
1. Use Django admin or create via management command
2. Strategies are stored in `TweetStrategy` model
3. Templates support placeholders like `{brand_name}`, `{brand_values}`

### Twitter Integration
- Uses Twitter API v2
- Credentials stored in encrypted variables table
- Supports posting, metrics refresh, and account management

### Image Generation
- Supports multiple providers (OpenAI DALL-E, Runware)
- Quality selection (low/high) routes to appropriate service
- Images stored in media directory

## Troubleshooting

### Common Issues
1. **Poetry not found**: Install Poetry using official installer
2. **Database errors**: Run `poetry run python manage.py migrate`
3. **Missing dependencies**: Run `poetry install`
4. **Twitter API errors**: Check API keys in admin variables table

### Logs
- Application logs: Check Django logs
- Cron job logs: `/var/log/gemnar_cron.log`
- Web server logs: Check nginx/apache logs

## Development Workflow
1. Create feature branch
2. Make changes
3. Test locally: `poetry run python manage.py test`
4. Create pull request
5. Deploy to staging/production

## Important Files
- `pyproject.toml` - Poetry configuration and dependencies
- `manage.py` - Django management script
- `website/models.py` - Core data models
- `website/management/commands/` - Background task commands
- `templates/` - Frontend templates