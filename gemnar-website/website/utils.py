from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def get_openai_api_key():
    """
    Get the OpenAI API key from the encrypted variables table only.
    Uses caching to avoid repeated database queries.
    """
    # Check cache first
    cache_key = "openai_api_key"
    cached_key = cache.get(cache_key)
    if cached_key:
        logger.debug("Retrieved OpenAI API key from cache")
        return cached_key

    try:
        from website.models import EncryptedVariable

        # Use the same approach as the status check for consistency
        openai_var = EncryptedVariable.objects.filter(
            key="OPENAI_API_KEY", is_active=True
        ).first()

        if not openai_var:
            logger.error("OpenAI API key not found in EncryptedVariable table")
            return None

        # Try to get the API key directly to check decryption
        api_key = openai_var.get_decrypted_value()
        if not api_key:
            logger.error(
                "OpenAI API key exists in database but decryption returned empty value"
            )
            return None

        # Validate key format
        if not api_key.startswith("sk-") or len(api_key) < 20:
            logger.error(
                f"OpenAI API key has invalid format (starts with {api_key[:10]}...)"
            )
            return None

        logger.debug(f"Successfully retrieved OpenAI API key (length: {len(api_key)})")
        # Cache for 1 hour
        cache.set(cache_key, api_key, 3600)
        return api_key

    except Exception as e:
        logger.error(f"Failed to get OpenAI API key from EncryptedVariable table: {e}")
        return None


def get_openai_client():
    """
    Get a configured OpenAI client instance.
    Uses OPENAI_API_KEY environment variable.
    Returns None if API key is not available.
    """
    try:
        from openai import OpenAI

        # Get API key from environment variables
        logger.info("Getting OpenAI API key from environment")
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            logger.error("Cannot create OpenAI client: No API key available")
            return None

        logger.debug(f"Creating OpenAI client with API key (length: {len(api_key)})")
        client = OpenAI(api_key=api_key)
        logger.debug("OpenAI client created successfully")
        return client

    except ImportError:
        logger.error("OpenAI library not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to create OpenAI client: {e}")
        return None


def extract_twitter_mentions(text):
    """
    Extract Twitter handles from text.
    Returns a list of unique handles (without @ symbol).
    """
    import re

    # Pattern to match Twitter handles: @username
    # Twitter usernames can contain letters, numbers, and underscores
    # They can be 1-15 characters long
    # Use word boundary to avoid matching email addresses
    pattern = r"(?<!\w)@([A-Za-z0-9_]{1,15})(?!\w)"

    matches = re.findall(pattern, text)
    # Return unique handles (case-insensitive)
    return list(set(handle.lower() for handle in matches))


def process_tweet_mentions(tweet, organization, user=None):
    """
    Process Twitter mentions in a tweet and create/update TwitterMention records.

    Args:
        tweet: BrandTweet instance
        organization: Organization instance
        user: User instance (optional, for created_by field)

    Returns:
        dict: Summary of processed mentions
    """
    from website.models import TwitterMention

    if not tweet.content:
        return {"processed": 0, "new": 0, "linked": 0}

    handles = extract_twitter_mentions(tweet.content)
    processed = 0
    new_mentions = 0
    auto_linked = 0

    for handle in handles:
        processed += 1

        # Get or create TwitterMention record
        mention, created = TwitterMention.objects.get_or_create(
            organization=organization,
            twitter_handle=handle,
            defaults={
                "first_mentioned_in": tweet,
                "created_by": user,
            },
        )

        if created:
            new_mentions += 1
            logger.info(f"Created new Twitter mention record for @{handle}")
        else:
            # Increment existing mention
            mention.increment_mentions(tweet)
            logger.info(f"Updated existing Twitter mention for @{handle}")

        # Try to auto-link to existing CRM records if not already linked
        if mention.mention_type == "unlinked":
            linked = auto_link_mention(mention, organization)
            if linked:
                auto_linked += 1

    return {
        "processed": processed,
        "new": new_mentions,
        "linked": auto_linked,
        "handles": handles,
    }


def auto_link_mention(mention, organization):
    """
    Attempt to automatically link a Twitter mention to existing CRM records.

    Args:
        mention: TwitterMention instance
        organization: Organization instance

    Returns:
        bool: True if successfully linked, False otherwise
    """
    from website.models import CRMCompany, CRMContact

    handle = mention.twitter_handle

    # First try to link to a company
    try:
        company = CRMCompany.objects.get(
            organization=organization, twitter_handle__iexact=handle
        )
        mention.link_to_company(company)
        logger.info(f"Auto-linked @{handle} to company: {company.name}")
        return True
    except CRMCompany.DoesNotExist:
        pass
    except CRMCompany.MultipleObjectsReturned:
        # If multiple companies have the same handle, log warning and don't auto-link
        logger.warning(f"Multiple companies found with Twitter handle @{handle}")
        pass

    # Then try to link to a contact
    try:
        contact = CRMContact.objects.get(
            organization=organization, twitter_handle__iexact=handle
        )
        mention.link_to_contact(contact)
        logger.info(f"Auto-linked @{handle} to contact: {contact.full_name}")
        return True
    except CRMContact.DoesNotExist:
        pass
    except CRMContact.MultipleObjectsReturned:
        # If multiple contacts have the same handle, log warning and don't auto-link
        logger.warning(f"Multiple contacts found with Twitter handle @{handle}")
        pass

    logger.info(f"Could not auto-link @{handle} - no matching CRM records found")
    return False


def suggest_crm_actions_for_mentions(organization, unlinked_only=True):
    """
    Suggest CRM actions for Twitter mentions (create contacts, link to companies, etc.)

    Args:
        organization: Organization instance
        unlinked_only: If True, only return suggestions for unlinked mentions

    Returns:
        list: List of suggested actions
    """
    from website.models import TwitterMention

    mentions_query = TwitterMention.objects.filter(organization=organization)
    if unlinked_only:
        mentions_query = mentions_query.filter(mention_type="unlinked")

    suggestions = []

    for mention in mentions_query.select_related("crm_company", "crm_contact"):
        suggestion = {
            "mention": mention,
            "handle": mention.twitter_handle,
            "times_mentioned": mention.times_mentioned,
            "actions": [],
        }

        if mention.mention_type == "unlinked":
            suggestion["actions"].extend(
                [
                    {
                        "type": "create_contact",
                        "description": f"Create new contact for @{mention.twitter_handle}",
                        "priority": "medium",
                    },
                    {
                        "type": "link_to_existing",
                        "description": f"Link @{mention.twitter_handle} to existing CRM record",
                        "priority": "low",
                    },
                ]
            )

        # High priority if mentioned multiple times
        if mention.times_mentioned >= 3:
            suggestion["actions"].append(
                {
                    "type": "high_priority_followup",
                    "description": f"High priority: @{mention.twitter_handle} mentioned {mention.times_mentioned} times",
                    "priority": "high",
                }
            )

        suggestions.append(suggestion)

    # Sort by priority and mention frequency
    suggestions.sort(
        key=lambda x: (
            x["times_mentioned"],
            len([a for a in x["actions"] if a["priority"] == "high"]),
        ),
        reverse=True,
    )

    return suggestions
