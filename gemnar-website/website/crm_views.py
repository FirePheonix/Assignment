from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from organizations.models import Organization
from .models import CRMContact, CRMCompany, CRMDeal, CRMActivity, CRMNote, CRMTask, User
import tweepy
import logging


def get_organization_or_404(request, organization_pk):
    """Helper function to get organization and check permissions"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    if request.user not in organization.users.all():
        messages.error(request, "You don't have access to this organization.")
        return None
    return organization


@login_required
def crm_dashboard(request, organization_pk):
    """CRM Dashboard with key metrics and recent activity"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    # Date filters
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    today - timedelta(days=30)

    # Basic counts
    total_contacts = CRMContact.objects.filter(organization=organization).count()
    total_companies = CRMCompany.objects.filter(organization=organization).count()
    total_deals = CRMDeal.objects.filter(organization=organization).count()

    # Deal pipeline metrics
    active_deals = CRMDeal.objects.filter(
        organization=organization,
        is_active=True,
        stage__in=["prospecting", "qualification", "proposal", "negotiation"],
    )

    pipeline_value = active_deals.aggregate(total=Sum("value"))

    # Calculate weighted value in Python (DB doesn't support F multiplication)
    weighted_total = 0
    for deal in active_deals.values("value", "probability"):
        if deal["value"] and deal["probability"]:
            weighted_total += deal["value"] * (deal["probability"] / 100)

    pipeline_value["weighted"] = weighted_total

    # Recent activity
    recent_activities = (
        CRMActivity.objects.filter(organization=organization)
        .select_related("contact", "deal", "assigned_to")
        .order_by("-created_at")[:10]
    )

    # Overdue tasks
    overdue_tasks = CRMTask.objects.filter(
        organization=organization,
        due_date__lt=timezone.now(),
        status__in=["pending", "in_progress"],
    ).count()

    # This week's metrics
    new_contacts_week = CRMContact.objects.filter(
        organization=organization, created_at__date__gte=week_ago
    ).count()

    new_companies_week = CRMCompany.objects.filter(
        organization=organization, created_at__date__gte=week_ago
    ).count()

    deals_closed_week = CRMDeal.objects.filter(
        organization=organization, actual_close_date__gte=week_ago, stage="closed_won"
    ).count()

    # Deal stage distribution
    deal_stages_raw = (
        CRMDeal.objects.filter(organization=organization, is_active=True)
        .values("stage")
        .annotate(count=Count("id"))
        .order_by("stage")
    )

    # Calculate percentages for each stage
    deal_stages = []
    for stage in deal_stages_raw:
        stage["percentage"] = (
            (stage["count"] / total_deals * 100) if total_deals > 0 else 0
        )
        deal_stages.append(stage)

    context = {
        "organization": organization,
        "total_contacts": total_contacts,
        "total_companies": total_companies,
        "total_deals": total_deals,
        "pipeline_value": pipeline_value,
        "recent_activities": recent_activities,
        "overdue_tasks": overdue_tasks,
        "new_contacts_week": new_contacts_week,
        "new_companies_week": new_companies_week,
        "deals_closed_week": deals_closed_week,
        "deal_stages": deal_stages,
    }

    return render(request, "organizations/crm/dashboard.html", context)


@login_required
def contact_list(request, organization_pk):
    """List all contacts with filtering and search"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    contacts = CRMContact.objects.filter(organization=organization)

    # Filters
    contact_type = request.GET.get("type")
    assigned_to = request.GET.get("assigned")
    search = request.GET.get("search")

    if contact_type:
        contacts = contacts.filter(contact_type=contact_type)

    if assigned_to:
        contacts = contacts.filter(assigned_to_id=assigned_to)

    if search:
        contacts = contacts.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
            | Q(company__icontains=search)
        )

    contacts = contacts.select_related("assigned_to").order_by("-created_at")

    # Pagination
    paginator = Paginator(contacts, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get team members for filter
    team_members = organization.users.all()

    context = {
        "organization": organization,
        "page_obj": page_obj,
        "team_members": team_members,
        "contact_types": CRMContact.CONTACT_TYPES,
        "current_filters": {
            "type": contact_type,
            "assigned": assigned_to,
            "search": search,
        },
    }

    return render(request, "organizations/crm/contact_list.html", context)


@login_required
def contact_detail(request, organization_pk, contact_pk):
    """Contact detail view with related activities and deals"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    contact = get_object_or_404(CRMContact, pk=contact_pk, organization=organization)

    # Related data
    deals = contact.deals.all().order_by("-created_at")
    activities = (
        contact.activities.all()
        .select_related("assigned_to")
        .order_by("-created_at")[:10]
    )
    notes = (
        contact.crm_notes.all()
        .select_related("created_by")
        .order_by("-created_at")[:10]
    )
    tasks = contact.tasks.filter(status__in=["pending", "in_progress"]).order_by(
        "due_date"
    )

    context = {
        "organization": organization,
        "contact": contact,
        "deals": deals,
        "activities": activities,
        "notes": notes,
        "tasks": tasks,
    }

    return render(request, "organizations/crm/contact_detail.html", context)


@login_required
def contact_create(request, organization_pk):
    """Create a new CRM contact"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    if request.method == "POST":
        # Extract form data
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        company = request.POST.get("company", "").strip()
        job_title = request.POST.get("job_title", "").strip()
        contact_type = request.POST.get("contact_type", "lead")
        lead_source = request.POST.get("lead_source", "")
        assigned_to_id = request.POST.get("assigned_to")
        description = request.POST.get("description", "").strip()
        tags = request.POST.get("tags", "").strip()

        # Basic validation
        if not first_name or not last_name or not email:
            messages.error(request, "First name, last name, and email are required.")
            return render(
                request,
                "organizations/crm/contact_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                },
            )

        # Check for duplicate email
        if CRMContact.objects.filter(organization=organization, email=email).exists():
            messages.error(
                request,
                f"A contact with email '{email}' already exists in this organization.",
            )
            return render(
                request,
                "organizations/crm/contact_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                },
            )

        try:
            # Get assigned user if provided
            assigned_to = None
            if assigned_to_id:
                assigned_to = organization.users.filter(id=assigned_to_id).first()

            # Create the contact
            contact = CRMContact.objects.create(
                organization=organization,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                company=company,
                job_title=job_title,
                contact_type=contact_type,
                lead_source=lead_source,
                assigned_to=assigned_to,
                description=description,
                tags=tags,
                created_by=request.user,
            )

            messages.success(
                request, f"Contact '{contact.full_name}' created successfully!"
            )
            return redirect(
                "crm_contact_detail",
                organization_pk=organization.pk,
                contact_pk=contact.pk,
            )

        except Exception as e:
            messages.error(request, f"Error creating contact: {str(e)}")
            return render(
                request,
                "organizations/crm/contact_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                },
            )

    # GET request - show the form
    context = {
        "organization": organization,
        "organization_users": organization.users.all(),
        "contact_types": CRMContact.CONTACT_TYPES,
        "lead_sources": CRMContact.LEAD_SOURCES,
    }
    return render(request, "organizations/crm/contact_create.html", context)


@login_required
def company_list(request, organization_pk):
    """List all companies in the CRM"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    # Get all companies for this organization
    companies = CRMCompany.objects.filter(organization=organization)

    # Search functionality
    search_query = request.GET.get("search", "").strip()
    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(website__icontains=search_query)
            | Q(industry__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    # Filter by assigned user
    assigned_to = request.GET.get("assigned_to")
    if assigned_to and assigned_to != "all":
        if assigned_to == "unassigned":
            companies = companies.filter(assigned_to__isnull=True)
        else:
            companies = companies.filter(assigned_to_id=assigned_to)

    # Filter by industry
    industry = request.GET.get("industry")
    if industry:
        companies = companies.filter(industry__icontains=industry)

    # Order by name
    companies = companies.select_related("assigned_to").order_by("name")

    # Pagination
    paginator = Paginator(companies, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "organization": organization,
        "companies": page_obj,
        "search_query": search_query,
        "assigned_to": assigned_to,
        "industry": industry,
        "organization_users": organization.users.all(),
        "total_companies": companies.count(),
    }

    return render(request, "organizations/crm/company_list.html", context)


@login_required
def company_create(request, organization_pk):
    """Create a new CRM company"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    if request.method == "POST":
        # Extract form data
        name = request.POST.get("name", "").strip()
        website = request.POST.get("website", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        industry = request.POST.get("industry", "").strip()
        twitter_handle = request.POST.get("twitter_handle", "").strip()
        instagram_handle = request.POST.get("instagram_handle", "").strip()
        linkedin_url = request.POST.get("linkedin_url", "").strip()
        assigned_to_id = request.POST.get("assigned_to")
        description = request.POST.get("description", "").strip()
        tags = request.POST.get("tags", "").strip()

        # Basic validation
        if not name or not website or not email:
            messages.error(request, "Company name, website, and email are required.")
            return render(
                request,
                "organizations/crm/company_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                },
            )

        # Check for duplicate company name
        if CRMCompany.objects.filter(organization=organization, name=name).exists():
            messages.error(
                request,
                f"A company with name '{name}' already exists in this organization.",
            )
            return render(
                request,
                "organizations/crm/company_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                },
            )

        try:
            # Get assigned user if provided
            assigned_to = None
            if assigned_to_id:
                assigned_to = organization.users.filter(id=assigned_to_id).first()

            # Clean social media handles
            twitter_handle = twitter_handle.lstrip("@")
            instagram_handle = instagram_handle.lstrip("@")

            # Create the company
            company = CRMCompany.objects.create(
                organization=organization,
                name=name,
                website=website,
                email=email,
                phone=phone,
                industry=industry,
                twitter_handle=twitter_handle,
                instagram_handle=instagram_handle,
                linkedin_url=linkedin_url,
                assigned_to=assigned_to,
                description=description,
                tags=tags,
                created_by=request.user,
            )

            messages.success(request, f"Company '{company.name}' created successfully!")
            return redirect(
                "crm_company_detail",
                organization_pk=organization.pk,
                company_pk=company.pk,
            )

        except Exception as e:
            messages.error(request, f"Error creating company: {str(e)}")
            return render(
                request,
                "organizations/crm/company_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                },
            )

    # GET request - show the form
    # Handle prefill parameters from URL
    prefill_data = {}
    if request.GET.get("prefill_name"):
        prefill_data["name"] = request.GET.get("prefill_name")
    if request.GET.get("prefill_email"):
        prefill_data["email"] = request.GET.get("prefill_email")

    context = {
        "organization": organization,
        "organization_users": organization.users.all(),
        "form_data": prefill_data,
    }
    return render(request, "organizations/crm/company_create.html", context)


@login_required
def company_detail(request, organization_pk, company_pk):
    """Company detail view with related contacts and deals"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    company = get_object_or_404(CRMCompany, pk=company_pk, organization=organization)

    # Related data
    contacts = (
        CRMContact.objects.filter(organization=organization, company=company.name)
        .select_related("assigned_to")
        .order_by("-created_at")[:10]
    )

    # Get deals through contacts that work for this company
    contact_emails = contacts.values_list("email", flat=True)
    deals = (
        CRMDeal.objects.filter(contact__email__in=contact_emails)
        .select_related("contact", "assigned_to")
        .order_by("-created_at")[:10]
    )

    context = {
        "organization": organization,
        "company": company,
        "contacts": contacts,
        "deals": deals,
    }

    return render(request, "organizations/crm/company_detail.html", context)


@login_required
def company_edit(request, organization_pk, company_pk):
    """Edit an existing CRM company"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    company = get_object_or_404(CRMCompany, pk=company_pk, organization=organization)

    if request.method == "POST":
        try:
            # Extract and validate form data
            name = request.POST.get("name", "").strip()
            website = request.POST.get("website", "").strip()
            email = request.POST.get("email", "").strip()
            phone = request.POST.get("phone", "").strip()
            industry = request.POST.get("industry", "").strip()
            twitter_handle = request.POST.get("twitter_handle", "").strip()
            instagram_handle = request.POST.get("instagram_handle", "").strip()
            linkedin_url = request.POST.get("linkedin_url", "").strip()
            assigned_to_id = request.POST.get("assigned_to")
            description = request.POST.get("description", "").strip()
            tags = request.POST.get("tags", "").strip()

            # Validation
            if not name:
                messages.error(request, "Company name is required")
                return render(
                    request,
                    "organizations/crm/company_edit.html",
                    {
                        "organization": organization,
                        "company": company,
                        "form_data": request.POST,
                        "organization_users": organization.users.all(),
                    },
                )

            if not website:
                messages.error(request, "Website is required")
                return render(
                    request,
                    "organizations/crm/company_edit.html",
                    {
                        "organization": organization,
                        "company": company,
                        "form_data": request.POST,
                        "organization_users": organization.users.all(),
                    },
                )

            if not email:
                messages.error(request, "Email is required")
                return render(
                    request,
                    "organizations/crm/company_edit.html",
                    {
                        "organization": organization,
                        "company": company,
                        "form_data": request.POST,
                        "organization_users": organization.users.all(),
                    },
                )

            # Check for duplicate company name (excluding current company)
            if (
                CRMCompany.objects.filter(organization=organization, name=name)
                .exclude(pk=company.pk)
                .exists()
            ):
                messages.error(request, f"A company with name '{name}' already exists")
                return render(
                    request,
                    "organizations/crm/company_edit.html",
                    {
                        "organization": organization,
                        "company": company,
                        "form_data": request.POST,
                        "organization_users": organization.users.all(),
                    },
                )

            # Format website URL
            if website and not website.startswith(("http://", "https://")):
                website = f"https://{website}"

            # Clean social media handles
            if twitter_handle.startswith("@"):
                twitter_handle = twitter_handle[1:]
            if instagram_handle.startswith("@"):
                instagram_handle = instagram_handle[1:]

            # Handle assigned_to
            assigned_to = None
            if assigned_to_id:
                try:
                    assigned_to = organization.users.get(pk=assigned_to_id)
                except User.DoesNotExist:
                    pass

            # Update company
            company.name = name
            company.website = website
            company.email = email
            company.phone = phone
            company.industry = industry
            company.twitter_handle = twitter_handle
            company.instagram_handle = instagram_handle
            company.linkedin_url = linkedin_url
            company.assigned_to = assigned_to
            company.description = description
            company.tags = tags
            company.save()

            messages.success(request, f"Company '{company.name}' updated successfully!")
            return redirect(
                "crm_company_detail",
                organization_pk=organization.pk,
                company_pk=company.pk,
            )

        except Exception as e:
            messages.error(request, f"Error updating company: {str(e)}")
            return render(
                request,
                "organizations/crm/company_edit.html",
                {
                    "organization": organization,
                    "company": company,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                },
            )

    # GET request - show the form with current data
    context = {
        "organization": organization,
        "company": company,
        "organization_users": organization.users.all(),
    }
    return render(request, "organizations/crm/company_edit.html", context)


@login_required
def deal_create(request, organization_pk):
    """Create a new CRM deal"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    if request.method == "POST":
        # Extract form data
        name = request.POST.get("name", "").strip()
        contact_id = request.POST.get("contact")
        description = request.POST.get("description", "").strip()
        stage = request.POST.get("stage", "prospecting")
        value = request.POST.get("value", "0").strip()
        currency = request.POST.get("currency", "USD")
        probability = request.POST.get("probability", "10").strip()
        expected_close_date = request.POST.get("expected_close_date")
        assigned_to_id = request.POST.get("assigned_to")

        # Basic validation
        if not name or not contact_id:
            messages.error(request, "Deal name and contact are required.")
            return render(
                request,
                "organizations/crm/deal_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                    "contacts": CRMContact.objects.filter(organization=organization),
                    "deal_stages": CRMDeal.DEAL_STAGES,
                    "currencies": CRMDeal.CURRENCIES,
                },
            )

        # Validate contact belongs to organization
        try:
            contact = CRMContact.objects.get(id=contact_id, organization=organization)
        except CRMContact.DoesNotExist:
            messages.error(request, "Selected contact does not exist.")
            return render(
                request,
                "organizations/crm/deal_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                    "contacts": CRMContact.objects.filter(organization=organization),
                    "deal_stages": CRMDeal.DEAL_STAGES,
                    "currencies": CRMDeal.CURRENCIES,
                },
            )

        # Validate and convert numeric fields
        try:
            value = float(value) if value else 0
            probability = int(probability) if probability else 10
            probability = max(0, min(100, probability))  # Clamp between 0-100
        except (ValueError, TypeError):
            messages.error(
                request, "Please enter valid numbers for value and probability."
            )
            return render(
                request,
                "organizations/crm/deal_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                    "contacts": CRMContact.objects.filter(organization=organization),
                    "deal_stages": CRMDeal.DEAL_STAGES,
                    "currencies": CRMDeal.CURRENCIES,
                },
            )

        # Parse expected close date
        parsed_close_date = None
        if expected_close_date:
            try:
                from datetime import datetime

                parsed_close_date = datetime.strptime(
                    expected_close_date, "%Y-%m-%d"
                ).date()
            except ValueError:
                messages.error(request, "Please enter a valid expected close date.")
                return render(
                    request,
                    "organizations/crm/deal_create.html",
                    {
                        "organization": organization,
                        "form_data": request.POST,
                        "organization_users": organization.users.all(),
                        "contacts": CRMContact.objects.filter(
                            organization=organization
                        ),
                        "deal_stages": CRMDeal.DEAL_STAGES,
                        "currencies": CRMDeal.CURRENCIES,
                    },
                )

        try:
            # Get assigned user if provided
            assigned_to = None
            if assigned_to_id:
                assigned_to = organization.users.filter(id=assigned_to_id).first()

            # Create the deal
            deal = CRMDeal.objects.create(
                organization=organization,
                contact=contact,
                name=name,
                description=description,
                stage=stage,
                value=value,
                currency=currency,
                probability=probability,
                expected_close_date=parsed_close_date,
                assigned_to=assigned_to,
                created_by=request.user,
            )

            messages.success(request, f"Deal '{deal.name}' created successfully!")
            return redirect(
                "crm_deal_detail",
                organization_pk=organization.pk,
                deal_pk=deal.pk,
            )

        except Exception as e:
            messages.error(request, f"Error creating deal: {str(e)}")
            return render(
                request,
                "organizations/crm/deal_create.html",
                {
                    "organization": organization,
                    "form_data": request.POST,
                    "organization_users": organization.users.all(),
                    "contacts": CRMContact.objects.filter(organization=organization),
                    "deal_stages": CRMDeal.DEAL_STAGES,
                    "currencies": CRMDeal.CURRENCIES,
                },
            )

    # GET request - show the form
    context = {
        "organization": organization,
        "organization_users": organization.users.all(),
        "contacts": CRMContact.objects.filter(organization=organization),
        "deal_stages": CRMDeal.DEAL_STAGES,
        "currencies": CRMDeal.CURRENCIES,
    }
    return render(request, "organizations/crm/deal_create.html", context)


@login_required
def deal_list(request, organization_pk):
    """List all deals with pipeline view"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    deals = CRMDeal.objects.filter(organization=organization)

    # Filters
    stage = request.GET.get("stage")
    assigned_to = request.GET.get("assigned")
    search = request.GET.get("search")

    if stage:
        deals = deals.filter(stage=stage)

    if assigned_to:
        deals = deals.filter(assigned_to_id=assigned_to)

    if search:
        deals = deals.filter(
            Q(name__icontains=search)
            | Q(contact__first_name__icontains=search)
            | Q(contact__last_name__icontains=search)
            | Q(contact__company__icontains=search)
        )

    deals = deals.select_related("contact", "assigned_to").order_by("-created_at")

    # Pipeline view
    pipeline_deals = {}
    for stage_choice in CRMDeal.DEAL_STAGES:
        stage_key = stage_choice[0]
        stage_deals = deals.filter(stage=stage_key)
        pipeline_deals[stage_choice[1]] = {
            "deals": stage_deals,
            "total_value": stage_deals.aggregate(Sum("value"))["value__sum"] or 0,
            "count": stage_deals.count(),
        }

    # Pagination for list view
    paginator = Paginator(deals, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get team members for filter
    team_members = organization.users.all()

    context = {
        "organization": organization,
        "page_obj": page_obj,
        "pipeline_deals": pipeline_deals,
        "team_members": team_members,
        "deal_stages": CRMDeal.DEAL_STAGES,
        "current_filters": {
            "stage": stage,
            "assigned": assigned_to,
            "search": search,
        },
    }

    return render(request, "organizations/crm/deal_list.html", context)


@login_required
def deal_detail(request, organization_pk, deal_pk):
    """Deal detail view with timeline and activities"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    deal = get_object_or_404(CRMDeal, pk=deal_pk, organization=organization)

    # Related data
    activities = (
        deal.activities.all().select_related("assigned_to").order_by("-created_at")
    )
    notes = deal.crm_notes.all().select_related("created_by").order_by("-created_at")
    tasks = deal.tasks.filter(status__in=["pending", "in_progress"]).order_by(
        "due_date"
    )

    # Stage progression
    stage_history = activities.filter(
        activity_type="note", description__icontains="stage"
    ).order_by("created_at")

    context = {
        "organization": organization,
        "deal": deal,
        "activities": activities,
        "notes": notes,
        "tasks": tasks,
        "stage_history": stage_history,
        "deal_stages": CRMDeal.DEAL_STAGES,
    }

    return render(request, "organizations/crm/deal_detail.html", context)


@login_required
def activity_list(request, organization_pk):
    """List activities and calendar view"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    activities = CRMActivity.objects.filter(organization=organization)

    # Filters
    activity_type = request.GET.get("type")
    status = request.GET.get("status")
    assigned_to = request.GET.get("assigned")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if activity_type:
        activities = activities.filter(activity_type=activity_type)

    if status:
        activities = activities.filter(status=status)

    if assigned_to:
        activities = activities.filter(assigned_to_id=assigned_to)

    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            activities = activities.filter(scheduled_at__date__gte=from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            activities = activities.filter(scheduled_at__date__lte=to_date)
        except ValueError:
            pass

    activities = activities.select_related("contact", "deal", "assigned_to").order_by(
        "-scheduled_at", "-created_at"
    )

    # Pagination
    paginator = Paginator(activities, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Overdue activities
    overdue_activities = CRMActivity.objects.filter(
        organization=organization, scheduled_at__lt=timezone.now(), status="planned"
    ).count()

    # Get team members for filter
    team_members = organization.users.all()

    context = {
        "organization": organization,
        "page_obj": page_obj,
        "overdue_activities": overdue_activities,
        "team_members": team_members,
        "activity_types": CRMActivity.ACTIVITY_TYPES,
        "activity_statuses": CRMActivity.ACTIVITY_STATUS,
        "current_filters": {
            "type": activity_type,
            "status": status,
            "assigned": assigned_to,
            "date_from": date_from,
            "date_to": date_to,
        },
    }

    return render(request, "organizations/crm/activity_list.html", context)


@login_required
def task_list(request, organization_pk):
    """List tasks with priority and due date sorting"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    tasks = CRMTask.objects.filter(organization=organization)

    # Filters
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    assigned_to = request.GET.get("assigned")
    overdue_only = request.GET.get("overdue")

    if status:
        tasks = tasks.filter(status=status)

    if priority:
        tasks = tasks.filter(priority=priority)

    if assigned_to:
        tasks = tasks.filter(assigned_to_id=assigned_to)

    if overdue_only:
        tasks = tasks.filter(
            due_date__lt=timezone.now(), status__in=["pending", "in_progress"]
        )

    tasks = tasks.select_related("contact", "deal", "assigned_to").order_by(
        "due_date", "-created_at"
    )

    # Pagination
    paginator = Paginator(tasks, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Task statistics
    task_stats = {
        "total": CRMTask.objects.filter(organization=organization).count(),
        "pending": CRMTask.objects.filter(
            organization=organization, status="pending"
        ).count(),
        "overdue": CRMTask.objects.filter(
            organization=organization,
            due_date__lt=timezone.now(),
            status__in=["pending", "in_progress"],
        ).count(),
    }

    # Get team members for filter
    team_members = organization.users.all()

    context = {
        "organization": organization,
        "page_obj": page_obj,
        "task_stats": task_stats,
        "team_members": team_members,
        "task_priorities": CRMTask.TASK_PRIORITIES,
        "task_statuses": CRMTask.TASK_STATUS,
        "current_filters": {
            "status": status,
            "priority": priority,
            "assigned": assigned_to,
            "overdue": overdue_only,
        },
    }

    return render(request, "organizations/crm/task_list.html", context)


@login_required
def crm_reports(request, organization_pk):
    """CRM Reports and Analytics"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organization_list")

    # Date range filter
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    # Default to last 30 days
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, "%Y-%m-%d").date()

    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

    # Sales metrics
    deals_in_period = CRMDeal.objects.filter(
        organization=organization, created_at__date__range=[date_from, date_to]
    )

    won_deals = deals_in_period.filter(stage="closed_won")
    lost_deals = deals_in_period.filter(stage="closed_lost")

    sales_metrics = {
        "total_deals": deals_in_period.count(),
        "won_deals": won_deals.count(),
        "lost_deals": lost_deals.count(),
        "total_value": won_deals.aggregate(Sum("value"))["value__sum"] or 0,
        "avg_deal_size": won_deals.aggregate(Avg("value"))["value__avg"] or 0,
        "win_rate": (won_deals.count() / deals_in_period.count() * 100)
        if deals_in_period.count() > 0
        else 0,
    }

    # Contact metrics
    contacts_in_period = CRMContact.objects.filter(
        organization=organization, created_at__date__range=[date_from, date_to]
    )

    contact_metrics = {
        "new_contacts": contacts_in_period.count(),
        "by_source": contacts_in_period.values("lead_source")
        .annotate(count=Count("id"))
        .order_by("-count"),
        "by_type": contacts_in_period.values("contact_type")
        .annotate(count=Count("id"))
        .order_by("-count"),
    }

    # Activity metrics
    activities_in_period = CRMActivity.objects.filter(
        organization=organization, created_at__date__range=[date_from, date_to]
    )

    activity_metrics = {
        "total_activities": activities_in_period.count(),
        "by_type": activities_in_period.values("activity_type")
        .annotate(count=Count("id"))
        .order_by("-count"),
        "completed": activities_in_period.filter(status="completed").count(),
    }

    # Team performance
    team_performance = []
    for user in organization.users.all():
        user_deals = deals_in_period.filter(assigned_to=user)
        user_activities = activities_in_period.filter(assigned_to=user)

        team_performance.append(
            {
                "user": user,
                "deals_created": user_deals.count(),
                "deals_won": user_deals.filter(stage="closed_won").count(),
                "activities_completed": user_activities.filter(
                    status="completed"
                ).count(),
                "revenue": user_deals.filter(stage="closed_won").aggregate(
                    Sum("value")
                )["value__sum"]
                or 0,
            }
        )

    context = {
        "organization": organization,
        "date_from": date_from,
        "date_to": date_to,
        "sales_metrics": sales_metrics,
        "contact_metrics": contact_metrics,
        "activity_metrics": activity_metrics,
        "team_performance": team_performance,
    }

    return render(request, "organizations/crm/reports.html", context)


# AJAX Views for quick actions
@login_required
def quick_add_note(request, organization_pk, contact_pk):
    """AJAX view to quickly add a note to a contact"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return JsonResponse({"error": "Access denied"}, status=403)

    contact = get_object_or_404(CRMContact, pk=contact_pk, organization=organization)

    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "Note content is required"}, status=400)

    note = CRMNote.objects.create(
        organization=organization,
        contact=contact,
        content=content,
        created_by=request.user,
    )

    return JsonResponse(
        {
            "success": True,
            "note": {
                "id": note.id,
                "content": note.content,
                "created_at": note.created_at.strftime("%Y-%m-%d %H:%M"),
                "created_by": note.created_by.username if note.created_by else "System",
            },
        }
    )


@login_required
def update_deal_stage(request, organization_pk, deal_pk):
    """AJAX view to update deal stage"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return JsonResponse({"error": "Access denied"}, status=403)

    deal = get_object_or_404(CRMDeal, pk=deal_pk, organization=organization)

    new_stage = request.POST.get("stage")
    if new_stage not in [choice[0] for choice in CRMDeal.DEAL_STAGES]:
        return JsonResponse({"error": "Invalid stage"}, status=400)

    old_stage = deal.stage
    deal.stage = new_stage

    # Update close date if deal is closed
    if new_stage in ["closed_won", "closed_lost"] and not deal.actual_close_date:
        deal.actual_close_date = timezone.now().date()

    deal.save()

    # Create activity log
    CRMActivity.objects.create(
        organization=organization,
        contact=deal.contact,
        deal=deal,
        activity_type="note",
        subject="Deal stage updated",
        description=f"Stage changed from {old_stage} to {new_stage}",
        status="completed",
        completed_at=timezone.now(),
        assigned_to=request.user,
        created_by=request.user,
    )

    return JsonResponse(
        {
            "success": True,
            "new_stage": new_stage,
            "stage_display": deal.get_stage_display(),
        }
    )


@login_required
def get_latest_tweet(request, organization_pk, company_pk):
    """Fetch the latest tweet for a company's Twitter handle"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return JsonResponse(
            {"success": False, "error": "Organization not found"}, status=404
        )

    get_object_or_404(CRMCompany, pk=company_pk, organization=organization)
    twitter_handle = request.GET.get("handle", "").strip()

    if not twitter_handle:
        return JsonResponse(
            {"success": False, "error": "Twitter handle is required"}, status=400
        )

    # Get the first brand with Twitter credentials for this organization
    # In a real scenario, you might want to specify which brand's credentials to use
    brand = organization.brands.filter(
        twitter_bearer_token__isnull=False, twitter_api_key__isnull=False
    ).first()

    if not brand:
        return JsonResponse(
            {
                "success": False,
                "error": "No Twitter credentials found. Please connect Twitter to your organization first.",
            },
            status=400,
        )

    try:
        # Initialize Twitter client
        client = tweepy.Client(
            bearer_token=brand.twitter_bearer_token,
            consumer_key=brand.twitter_api_key,
            consumer_secret=brand.twitter_api_secret,
            access_token=brand.twitter_access_token,
            access_token_secret=brand.twitter_access_token_secret,
            wait_on_rate_limit=True,
        )

        # Get user by username
        user = client.get_user(username=twitter_handle)
        if not user.data:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Twitter user @{twitter_handle} not found",
                },
                status=404,
            )

        user_id = user.data.id

        # Get latest tweets from user
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=5,
            tweet_fields=[
                "created_at",
                "public_metrics",
                "lang",
                "source",
                "context_annotations",
                "entities",
                "referenced_tweets",
            ],
            user_fields=["username", "name", "profile_image_url"],
        )

        if not tweets.data:
            return JsonResponse(
                {"success": False, "error": f"No tweets found for @{twitter_handle}"},
                status=404,
            )

        # Get the latest tweet
        latest_tweet = tweets.data[0]

        # Format the created_at date nicely
        from django.utils import timezone as django_timezone
        import dateutil.parser

        created_at = dateutil.parser.parse(latest_tweet.created_at)
        now = django_timezone.now()
        time_diff = now - created_at

        if time_diff.days > 0:
            time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            time_ago = "Just now"

        # Build response data
        tweet_data = {
            "id": latest_tweet.id,
            "text": latest_tweet.text,
            "created_at": time_ago,
            "created_at_full": created_at.strftime("%B %d, %Y at %I:%M %p"),
            "public_metrics": latest_tweet.public_metrics,
            "lang": getattr(latest_tweet, "lang", None),
            "source": getattr(latest_tweet, "source", None),
        }

        # Add additional analytics if available
        additional_data = {}
        if (
            hasattr(latest_tweet, "context_annotations")
            and latest_tweet.context_annotations
        ):
            additional_data["context_annotations"] = latest_tweet.context_annotations
        if hasattr(latest_tweet, "entities") and latest_tweet.entities:
            additional_data["entities"] = latest_tweet.entities
        if (
            hasattr(latest_tweet, "referenced_tweets")
            and latest_tweet.referenced_tweets
        ):
            additional_data["referenced_tweets"] = latest_tweet.referenced_tweets

        return JsonResponse(
            {
                "success": True,
                "tweet": tweet_data,
                "tweet_data": additional_data,
                "user_data": {
                    "username": user.data.username,
                    "name": user.data.name,
                    "profile_image_url": getattr(user.data, "profile_image_url", None),
                },
            }
        )

    except tweepy.Unauthorized:
        logging.error(f"Twitter API unauthorized for organization {organization_pk}")
        return JsonResponse(
            {
                "success": False,
                "error": "Twitter API authentication failed. Please check your credentials.",
            },
            status=401,
        )

    except tweepy.Forbidden as e:
        logging.error(
            f"Twitter API forbidden for organization {organization_pk}: {str(e)}"
        )
        return JsonResponse(
            {
                "success": False,
                "error": "Access forbidden. The account may be private or suspended.",
            },
            status=403,
        )

    except tweepy.NotFound:
        return JsonResponse(
            {"success": False, "error": f"Twitter user @{twitter_handle} not found"},
            status=404,
        )

    except tweepy.TooManyRequests:
        logging.warning(
            f"Twitter API rate limit exceeded for organization {organization_pk}"
        )
        return JsonResponse(
            {
                "success": False,
                "error": "Twitter API rate limit exceeded. Please try again later.",
            },
            status=429,
        )

    except Exception as e:
        logging.error(
            f"Unexpected error fetching tweet for @{twitter_handle}: {str(e)}"
        )
        return JsonResponse(
            {
                "success": False,
                "error": "An unexpected error occurred. Please try again.",
            },
            status=500,
        )


@login_required
def twitter_mentions_dashboard(request, organization_pk):
    """Dashboard showing Twitter mentions tracked from tweets"""
    organization = get_organization_or_404(request, organization_pk)
    if not organization:
        return redirect("organizations:list")

    from .models import TwitterMention
    from .utils import suggest_crm_actions_for_mentions

    # Get all Twitter mentions for this organization
    mentions = (
        TwitterMention.objects.filter(organization=organization)
        .select_related("crm_company", "crm_contact", "first_mentioned_in")
        .order_by("-last_mentioned_at")
    )

    # Filter by type if requested
    mention_type = request.GET.get("type")
    if mention_type in ["company", "contact", "unlinked"]:
        mentions = mentions.filter(mention_type=mention_type)

    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        mentions = mentions.filter(
            Q(twitter_handle__icontains=search_query)
            | Q(crm_company__name__icontains=search_query)
            | Q(crm_contact__first_name__icontains=search_query)
            | Q(crm_contact__last_name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(mentions, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_mentions = TwitterMention.objects.filter(organization=organization).count()
    unlinked_mentions = TwitterMention.objects.filter(
        organization=organization, mention_type="unlinked"
    ).count()
    company_mentions = TwitterMention.objects.filter(
        organization=organization, mention_type="company"
    ).count()
    contact_mentions = TwitterMention.objects.filter(
        organization=organization, mention_type="contact"
    ).count()

    # Get suggestions for unlinked mentions
    suggestions = suggest_crm_actions_for_mentions(organization, unlinked_only=True)

    context = {
        "organization": organization,
        "mentions": page_obj,
        "total_mentions": total_mentions,
        "unlinked_mentions": unlinked_mentions,
        "company_mentions": company_mentions,
        "contact_mentions": contact_mentions,
        "suggestions": suggestions[:10],  # Show top 10 suggestions
        "current_filter": mention_type,
        "search_query": search_query,
    }

    return render(request, "organizations/crm/twitter_mentions.html", context)
