# website/forms.py
from organizations.forms import OrganizationForm as BaseOrganizationForm


class CustomOrganizationForm(BaseOrganizationForm):
    def __init__(self, *args, **kwargs):
        # Extract request before passing to the ultimate superclass (ModelForm)
        request = kwargs.pop("request", None)
        self.request = request

        # Determine if this is a new instance before initialization
        is_new_instance = "instance" not in kwargs or kwargs["instance"] is None

        # Call ModelForm's __init__ directly, bypassing BaseOrganizationForm's __init__
        # This ensures self.instance and self.fields are populated without the problematic queryset assignment.
        super(BaseOrganizationForm, self).__init__(*args, **kwargs)

        # Now, conditionally handle the 'owner' field based on whether it's a new instance
        if is_new_instance:
            # For new organizations, the owner is set automatically after creation,
            # so the field is not needed in the form.
            self.fields.pop("owner", None)
        else:
            # For existing organizations, ensure the owner field's queryset is correctly set
            # and initial value is populated, as BaseOrganizationForm intended.
            # This logic was already present in CustomOrganizationForm's original 'else' block.
            if (
                "owner" in self.fields
            ):  # Check if owner field exists (it should for existing instances)
                self.fields["owner"].queryset = self.instance.organization_users.filter(
                    is_admin=True, user__is_active=True
                )
                if self.instance.owner:
                    self.fields["owner"].initial = self.instance.owner.organization_user

    def save(self, commit=True):
        # Handle new instances by calling ModelForm's save directly
        if not self.instance.pk:
            # For new instances, bypass BaseOrganizationForm's save method
            # and call ModelForm's save directly
            from django.forms import ModelForm

            return ModelForm.save(self, commit=commit)
        else:
            # For existing instances, use the BaseOrganizationForm's save method
            return super().save(commit=commit)
