import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.models import BookInstance


class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text="Enter a date between now and 4 weeks (default 3).")

    # NOTE:
    # Django provides numerous places where you can validate your data.
    # The easiest way to validate a single field is to override the method
    # clean_<fieldname>() for the field you want to check.
    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # Check if a date is not in the past.
        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

        # Remember to always return the cleaned data.
        return data


# If you just need a form to map the fields of a single model then your model will already define
# most of the information that you need in your form: fields, labels, help text and so on. 
# Rather than recreating the model definitions in your form, it is easier to use the ModelForm
# helper class to create the form from your model. This ModelForm can then be used within your
# views in exactly the same way as an ordinary Form.
class RenewBookModelForm(forms.ModelForm):
    def clean_due_back(self):
        data = self.cleaned_data['due_back']

        # Check if a date is not in the past.
        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

        # Remember to always return the cleaned data.
        return data

    class Meta:
        # You can also include all fields in the form using fields = '__all__', or you can use
        # exclude (instead of fields) to specify the fields not to include from the model).
        # Neither approach is recommended because new fields added to the model are then
        # automatically included in the form (without the developer necessarily considering
        # possible security implications).
        #
        # The rest of the information comes from the model field definitions (e.g. labels, widgets,
        # help text, error messages). If these aren't quite right, then we can override them in our
        # class Meta, specifying a dictionary containing the field to change and its new value.
        model = BookInstance
        fields = ['due_back']
        labels = {'due_back': _('New renewal date')}
        help_texts = {'due_back': _('Enter a date between now and 4 weeks (default 3).')}
