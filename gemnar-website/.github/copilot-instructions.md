# Gemnar Website Development Instructions

**ALWAYS follow these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

Bootstrap, build, and test the repository:

### Prerequisites and Installation
- Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- Add Poetry to PATH: `export PATH="/home/runner/.local/bin:$PATH"`
- Verify installation: `poetry --version`

### Core Development Commands
- **Install dependencies**: `poetry install` -- takes 30 seconds. NEVER CANCEL. Set timeout to 90+ seconds.
- **Run database migrations**: `poetry run python manage.py migrate` -- takes 20 seconds. NEVER CANCEL. Set timeout to 60+ seconds.
- **Run tests**: `poetry run python manage.py test --failfast` -- takes 60 seconds. NEVER CANCEL. Set timeout to 120+ seconds.
- **Check migration status**: `poetry run python manage.py showmigrations`
- **Create new migrations**: `poetry run python manage.py makemigrations`
- **Collect static files**: `poetry run python manage.py collectstatic --noinput` -- takes 2 seconds.
- **Run linting**: `poetry run ruff check .` -- takes 1 second.
- **Run formatting**: `poetry run ruff format .` -- takes 1 second.

### Development Server
- **Primary method**: `poetry run uvicorn gemnar.asgi:application --reload --reload-dir website/templates --host 127.0.0.1 --port 8000`
- **Alternative**: `./run.sh` (includes comprehensive reload configuration)
- **Legacy method**: `poetry run python manage.py runserver` (less preferred for development)
- Access at: http://127.0.0.1:8000/

## Validation

### Always run complete validation after making changes:
1. **Build validation**: Run `poetry install` if dependencies changed
2. **Migration validation**: Run `poetry run python manage.py migrate` after model changes  
3. **Test validation**: Run `poetry run python manage.py test --failfast` to ensure no regressions
4. **Lint validation**: Run `poetry run ruff check .` and `poetry run ruff format .`
5. **Static file validation**: Run `poetry run python manage.py collectstatic --noinput`
6. **Server validation**: Start server and test http://127.0.0.1:8000/ returns 200 OK

### Manual Testing Scenarios
After making changes, ALWAYS test these user scenarios:
- **Basic functionality**: Access homepage at http://127.0.0.1:8000/ and verify 200 response
- **Admin access**: Visit custom admin URL at /admin-lkj234234ljk8c8/ (302 redirect is expected)
- **API endpoints**: Test API endpoints like /api/users/profile/ (401 auth required is expected)
- **Authentication flow**: Test login/logout if modifying auth systems

### CI Compatibility
- ALWAYS run `poetry run python manage.py test --failfast` before committing
- ALWAYS run `poetry run ruff check .` and `poetry run ruff format .` before committing
- The CI pipeline (.github/workflows/test.yml) will fail if tests or linting fail

## Architecture Overview

### Technology Stack
- **Framework**: Django 5.x with Python 3.11+
- **Dependency Management**: Poetry (NOT pip or conda)
- **Database**: PostgreSQL in production, SQLite for local development
- **ASGI Server**: Uvicorn (NOT gunicorn for development)
- **Task Processing**: Cron-based approach (NOT Celery)
- **APIs**: Twitter API v2, OpenAI API, Stripe API

### Background Task Processing
**IMPORTANT**: This project does NOT use Celery. Instead:
- Cron job runs every minute: `poetry run python manage.py run_every_minute`
- Key management commands:
  - `send_brand_tweets` - Posts scheduled tweets
  - `send_brand_instagram_posts` - Processes Instagram posts  
  - `setup_twitter_auth` - Configures Twitter API credentials
  - `collect_system_stats` - Gathers system metrics

### Project Structure
- `manage.py` - Django management script
- `gemnar/` - Main Django project settings
- `website/` - Primary Django app with models, views, templates
- `chat/` - Chat functionality Django app
- `website/management/commands/` - Custom Django management commands
- `ansible/` - Deployment automation scripts
- `static/` - Static assets (CSS, JS, images)
- `templates/` - Django templates
- `pyproject.toml` - Poetry configuration and dependencies

## Common Development Workflows

### Adding New Features
1. Create database migrations: `poetry run python manage.py makemigrations`
2. Apply migrations: `poetry run python manage.py migrate`
3. Test changes: `poetry run python manage.py test`
4. Test locally: Start server and validate functionality

### Working with Models
- Models are in `website/models.py`
- After model changes: `poetry run python manage.py makemigrations website`
- Apply changes: `poetry run python manage.py migrate`
- Check migration status: `poetry run python manage.py showmigrations`
- Test in shell: `poetry run python manage.py shell`

### Working with Templates
- Templates in `website/templates/` and `templates/`
- Live reload enabled when using uvicorn with `--reload-dir website/templates`
- CSS/JS changes auto-reload with proper uvicorn configuration

### Working with APIs
- API views in `website/api_views.py`
- DRF authentication enabled (Token + Session)
- Test API endpoints after changes using curl or Django test client
- Many API endpoints available under `/api/` path (see website/urls.py)

### Background Tasks
- Use management commands in `website/management/commands/`
- Main command: `poetry run python manage.py run_every_minute --dry-run` (test mode)
- Tweet processing: `poetry run python manage.py send_brand_tweets --dry-run`
- Instagram posts: `poetry run python manage.py send_brand_instagram_posts --dry-run`

## Environment Configuration

### Required Environment Variables
The application references these environment variables (typically in production):
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - For AI tweet generation
- `TWITTER_API_KEY`, `TWITTER_API_SECRET`, etc. - Twitter API credentials
- `ENVIRONMENT` - Set to 'development' for local development

### Local Development
- No `.env` file required for basic development
- SQLite database created automatically
- Most features work without API keys for basic development

## Deployment

### Production Deployment
- Uses Ansible playbooks in `ansible/` directory
- Quick deploy: `cd ansible && ./quick-deploy.sh`
- Full deployment: `cd ansible && ansible-playbook -i inventory.yml playbook.yml`
- GitHub Actions deployment on push to main branch

### Static Files
- Collected to `staticfiles/` directory
- Always run `poetry run python manage.py collectstatic --noinput` before deployment
- Static file collection warnings about duplicate files are NORMAL and can be ignored
- Pre-commit hooks automatically run collectstatic during commits

### Expected Warnings (Normal)
- SyntaxWarning messages from tweepy library - these are harmless
- Deprecation warnings from dj_rest_auth - these are known and do not affect functionality
- Static file duplicate warnings during collectstatic - these are expected

## Troubleshooting

### Common Issues
- **Poetry not found**: Install with official installer, ensure PATH includes `~/.local/bin`
- **Database errors**: Run `poetry run python manage.py migrate`
- **Missing dependencies**: Run `poetry install` 
- **Import errors**: Ensure Poetry virtual environment is activated
- **Port conflicts**: Change port in uvicorn command (`--port 8001`)

### Performance Considerations
- SQLite is fine for development but use PostgreSQL for production
- Background tasks run via cron, not real-time processing
- Static files should be served by web server in production

### Debug Information
- Django debug mode enabled automatically in development
- Check logs in `logs/` directory when using `./run.sh`
- Use `poetry run python manage.py shell` for interactive debugging

## Security Notes
- Never commit API keys or secrets to the repository
- Use environment variables for sensitive configuration
- Pre-commit hooks automatically scan for secrets using gitleaks

## Testing Guidelines
- Write tests in `website/tests*.py` files
- Use Django TestCase for database-dependent tests
- Mock external API calls in tests
- Aim for fast test execution (current suite: ~50 seconds)

Always validate your changes meet these guidelines before submitting code.