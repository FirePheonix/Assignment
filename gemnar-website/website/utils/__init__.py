# Re-export get_openai_client for backward compatibility
import importlib.util
import os

# Import from the utils.py module in the same directory as the utils folder
spec = importlib.util.spec_from_file_location(
    "utils", os.path.join(os.path.dirname(__file__), "..", "utils.py")
)
utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_module)

get_openai_client = utils_module.get_openai_client
get_openai_api_key = utils_module.get_openai_api_key
extract_twitter_mentions = utils_module.extract_twitter_mentions
process_tweet_mentions = utils_module.process_tweet_mentions
auto_link_mention = utils_module.auto_link_mention
suggest_crm_actions_for_mentions = utils_module.suggest_crm_actions_for_mentions

__all__ = [
    "get_openai_client",
    "get_openai_api_key",
    "extract_twitter_mentions",
    "process_tweet_mentions",
    "auto_link_mention",
    "suggest_crm_actions_for_mentions",
]
