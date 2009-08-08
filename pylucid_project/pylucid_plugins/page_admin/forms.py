# coding:utf-8

from django import forms
from django.template import mark_safe
from django.forms.util import ErrorList
from django.forms import ModelForm
from django.forms.models import BaseModelFormSet, modelformset_factory
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext as _

from django_tools.middlewares import ThreadLocal

from pylucid.models import PageTree, PageMeta, PageContent, PluginPage, Design, Language


class EditPageForm(forms.Form):
    """ Form for "quick inline" edit. """
    edit_comment = forms.CharField(
        max_length=255, required=False,
        help_text=_("The reason for editing."),
        widget=forms.TextInput(attrs={'class':'bigger'}),
    )

    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': '15'}),
    )



class PageTreeForm(forms.ModelForm):
    def clean(self):
        """ Validate if page with same slug and parent exist. """
        cleaned_data = self.cleaned_data

        if "slug" not in cleaned_data or "parent" not in cleaned_data:
            # Only do something if both fields are valid so far.
            return cleaned_data

        slug = cleaned_data["slug"]
        parent = cleaned_data["parent"]
        exists = PageTree.on_site.all().filter(slug=slug, parent=parent).count()
        if exists:
            if parent == None: # parent is the tree root
                parent_url = "/"
            else:
                parent_url = parent.get_absolute_url()
            msg = "Page '%s<strong>%s</strong>/' exists already." % (parent_url, slug)
            self._errors["slug"] = ErrorList([mark_safe(msg)])

        return cleaned_data

    def __init__(self, *args, **kwargs):
        """ Change form field data in a DRY way """
        super(PageTreeForm, self).__init__(*args, **kwargs)
        designs = Design.on_site.values_list("id", "name")
        self.fields['design'].choices = [("", "---------")] + list(designs)

        self.fields["parent"].widget = forms.widgets.Select(choices=PageTree.objects.get_choices())

    class Meta:
        model = PageTree
        exclude = ("page_type", "site")


class PageMetaForm(ModelForm):
    class Meta:
        model = PageMeta
        exclude = ("page", "lang")


class PageContentForm(ModelForm):
    class Meta:
        model = PageContent
        exclude = ("pagemeta",)


class PluginPageForm(ModelForm):
#    app_label = forms.TypedChoiceField(
#        choices=PluginPage.objects.get_app_choices(), label=_('App label'),
#        help_text=_('The app lable witch is in settings.INSTALLED_APPS')
#    )
    def __init__(self, *args, **kwargs):
        """ Change form field data in a DRY way """
        super(PluginPageForm, self).__init__(*args, **kwargs)
        self.fields["app_label"].widget = forms.widgets.Select(choices=PluginPage.objects.get_app_choices())

    class Meta:
        model = PluginPage
        exclude = ("pagemeta")
