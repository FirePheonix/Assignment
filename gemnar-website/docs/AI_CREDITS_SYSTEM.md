# AI Credits System Documentation

## Overview

The AI Credits system allows brands to purchase and manage credits for using AI services like Runware image generation. This system provides transparency, control, and tracking of AI service usage costs.

## Key Components

### 1. Models

#### Brand Model Changes
- **`credits_balance`**: Decimal field storing current credit balance
- **Credit Management Methods**:
  - `has_sufficient_credits(amount)`: Check if brand has enough credits
  - `deduct_credits(amount, description, type)`: Deduct credits with transaction log
  - `add_credits(amount, description, type)`: Add credits with transaction log

#### CreditTransaction Model
Tracks all credit transactions with:
- `brand`: Associated brand
- `transaction_type`: purchase, usage, refund, bonus, adjustment
- `amount`: Credit amount (positive for additions, negative for deductions)
- `description`: Human-readable description
- `balance_after`: Credit balance after this transaction
- `service_used`: AI service used (for usage transactions)
- `api_request_id`: API request ID for tracking
- `payment_intent_id`: Payment processor reference

#### CreditPackage Model
Defines purchasable credit packages with:
- `name`: Package name (e.g., "Starter Pack")
- `credits_amount`: Base credits included
- `bonus_credits`: Extra bonus credits
- `price_usd`/`price_inr`: Pricing in different currencies
- Stripe and Cashfree integration fields

### 2. Credit Manager Utility

The `CreditManager` class provides helper methods:

```python
from website.utils.credit_manager import CreditManager

# Get service cost
cost = CreditManager.get_service_cost("Image Generation")

# Check credits
has_credits = CreditManager.check_sufficient_credits(brand, cost)

# Deduct credits
success, message = CreditManager.deduct_credits(
    brand=brand,
    amount=cost,
    description="Generated image via Runware API",
    service_used="runware_image_generation",
    api_request_id="req_123"
)

# Add credits
success, message = CreditManager.add_credits(
    brand=brand,
    amount=10.00,
    description="Credit package purchase",
    payment_intent_id="pi_stripe_123"
)
```

### 3. Runware Integration

The system automatically:
1. **Checks credits** before making Runware API calls
2. **Returns error** if insufficient credits with balance information
3. **Deducts credits** only after successful image generation
4. **Logs transaction** with API request details

Example error response:
```json
{
    "success": false,
    "error": "Insufficient credits. Need 0.02 credits, but balance is 0.00. Please add credits to continue.",
    "credits_needed": "0.02",
    "current_balance": "0.00"
}
```

Example success response:
```json
{
    "success": true,
    "message": "Image generated successfully!",
    "image_url": "/media/brand_tweets/image.png",
    "service": "Runware AI",
    "credits_used": "0.02",
    "credits_remaining": "4.98"
}
```

## API Endpoints

### Get Brand Credit Info
`GET /organizations/{org_id}/brands/{brand_id}/credits/info/`

Returns credit balance, statistics, and recent transactions.

### Get Credit Packages
`GET /api/credits/packages/`

Returns available credit packages for purchase.

### Simulate Credit Usage (Testing)
`POST /organizations/{org_id}/brands/{brand_id}/credits/test-usage/`

Simulates credit usage for testing purposes.

### Add Test Credits (Development)
`POST /organizations/{org_id}/brands/{brand_id}/credits/add-test/`

Adds test credits for development/testing (admin only).

## Admin Interface

### Brand Admin
- Credit balance displayed in list view with color coding:
  - Red: < $1.00
  - Orange: $1.00 - $9.99  
  - Green: ≥ $10.00
- "AI Credits" section in brand edit form

### Credit Transaction Admin
- List view with filters by transaction type, brand, date
- Read-only fields for balance_after, created_at
- Search by brand name, description, service used

### Credit Package Admin
- List view showing credits, pricing, and value ratios
- Toggle active/featured status
- Ordering by sort_order and price

## Management Commands

### Setup Credit System
```bash
poetry run python manage.py setup_credit_system --free-credits 5.0
```

Options:
- `--free-credits X`: Give X free credits to existing brands (default: 5.0)
- `--dry-run`: Show what would be done without making changes

## Default Pricing

Current default costs (fallback if no RunwarePricingData):
- Image Generation: $0.02 per image
- Text Generation: $0.001 per request
- Image Upscaling: $0.005 per image
- Background Removal: $0.003 per image

## Initial Credit Packages

Created by migration `0053_create_initial_credit_packages`:

1. **Starter Pack**: 2 credits + 0 bonus for $5.00 (0.40 credits/$)
2. **Creator Pack**: 10 credits + 2 bonus for $20.00 (0.60 credits/$) ⭐
3. **Professional Pack**: 25 credits + 5 bonus for $45.00 (0.67 credits/$) ⭐
4. **Enterprise Pack**: 50 credits + 15 bonus for $80.00 (0.81 credits/$)

## Usage Examples

### Check if brand can use service
```python
cost = CreditManager.get_service_cost("Image Generation")
if not brand.has_sufficient_credits(cost):
    # Show credit purchase options
    packages = CreditManager.get_available_packages()
```

### Process successful AI service usage
```python
success, message = CreditManager.deduct_credits(
    brand=brand,
    amount=cost,
    description=f"Generated image for tweet {tweet.id}",
    service_used="runware_image_generation",
    api_request_id=response_uuid
)
```

### Get credit statistics
```python
stats = CreditManager.get_credit_stats(brand)
# Returns: current_balance, total_purchased, total_used, recent_usage_30d, transaction_count
```

## Security Considerations

1. **Credit checks before API calls**: Prevents unnecessary API usage
2. **Transaction logging**: Full audit trail of all credit operations
3. **User permissions**: Only organization members can view/manage credits
4. **Admin controls**: Test credit functions require admin access
5. **Atomic operations**: Credit operations use database transactions

## Integration with Payment Systems

The system is designed to integrate with:
- **Stripe**: `stripe_price_id_usd` and `stripe_price_id_inr` fields
- **Cashfree**: `cashfree_product_id` field

Payment webhooks should call `CreditManager.purchase_credits()` upon successful payment.

## Monitoring and Analytics

Credit usage can be monitored through:
- Django admin interface
- Credit transaction logs
- Brand credit statistics
- API endpoints for frontend integration