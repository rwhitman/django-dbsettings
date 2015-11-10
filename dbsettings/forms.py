import re
import copy

from collections import OrderedDict
import django
from django import forms
from django.utils.text import capfirst
if django.VERSION < (1, 8):
    from django.db.models import get_model
else:
    from django.apps import apps
    get_model = apps.get_model

from dbsettings.loading import get_setting_storage


RE_FIELD_NAME = re.compile(r'^(.+)__(.*)__(.+)$')


class SettingsEditor(forms.BaseForm):
    "Base editor, from which customized forms are created"

    def __iter__(self):
        for field in super(SettingsEditor, self).__iter__():
            yield self.specialize(field)

    def __getitem__(self, name):
        field = super(SettingsEditor, self).__getitem__(name)
        return self.specialize(field)

    def specialize(self, field):
        "Wrapper to add module_name and class_name for regrouping"
        field.label = capfirst(field.label)
        module_name, class_name, _ = RE_FIELD_NAME.match(field.name).groups()

        app_label = self.apps[field.name]
        field.module_name = app_label

        if class_name:
            model = get_model(app_label, class_name)
            if model:
                class_name = model._meta.verbose_name
        field.class_name = class_name
        field.verbose_name = self.verbose_names[field.name]

        return field


def customized_editor(user, settings):
    "Customize the setting editor based on the current user and setting list"
    base_fields = OrderedDict()
    verbose_names = {}
    apps = {}
    for setting in settings:
        if setting.show_in_editor :
            perm = '%s.can_edit_%s_settings' % (
                setting.app,
                setting.class_name.lower()
            )
            if user.has_perm(perm):
                # Add the field to the customized field list
                storage = get_setting_storage(*setting.key)
                kwargs = {
                    'label': setting.description,
                    'help_text': setting.help_text,
                    # Provide current setting values for initializing the form
                    'initial': setting.to_editor(storage.value),
                    'required': setting.required,
                }
                if setting.choices:
                    field = forms.ChoiceField(choices=setting.choices, **kwargs)
                else:
                    field = setting.field(**kwargs)
                key = '%s__%s__%s' % setting.key
                apps[key] = setting.app
                base_fields[key] = field
                if setting.readonly :
                    # Simply setting this on the field sets all the fields of this type, make a copy of the field obj
                    base_fields[key] = copy.deepcopy(field)
                    base_fields[key].widget.attrs = {'readonly':'readonly'}
                verbose_names[key] = setting.verbose_name
    attrs = {'base_fields': base_fields, 'verbose_names': verbose_names, 'apps': apps}
    return type('SettingsEditor', (SettingsEditor,), attrs)
