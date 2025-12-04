def default_brand_and_credits(request):
    """Inject default brand and its credits into templates.

    Exposes:
    - current_brand: the user's default brand (or first brand) if any
    - current_brand_credits: Decimal balance or None
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"current_brand": None, "current_brand_credits": None}

    # Lazy import to avoid circular imports
    from django.db.models import Q
    from website.models import Brand

    # Find brands owned by the user or where they're in the org
    brands_qs = Brand.objects.filter(Q(owner=user) | Q(organization__users=user))
    if not brands_qs.exists():
        return {"current_brand": None, "current_brand_credits": None}

    # Prefer default brand, else first
    brand = brands_qs.filter(is_default=True).first() or brands_qs.first()
    return {
        "current_brand": brand,
        "current_brand_credits": getattr(brand, "credits_balance", None),
    }
