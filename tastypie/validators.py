from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

class Validator(object):
    message = 'Please check your input'
    def __init__(self, bundle, title, *args, **kwargs):
        self.bundle = bundle
        self.title = title
        self.args = args
        self.kwargs = kwargs

    def get_error_message(self):
        return self.message % {'title':self.title}

    def validate(self, value):
        raise NotImplementedError


class UniqueValidator(Validator):
    message = 'Choose another %(title)s'

    def __init__(self, bundle, title, list_set, *args, **kwargs):
        super(UniqueValidator, self).__init__(bundle, title, *args, **kwargs)
        self.list_set = self.get_list_set(list_set)

    def get_list_set(self, list_set):
        if self.kwargs.get('case_sensitive', False):
            list_set = [x.lower() for x in list_set]

        return list_set

    def validate(self, value):
        is_valid = True

        if self.kwargs.get('case_sensitive', False):
            value = value.lower()

        if self.bundle is None or self.bundle.request.method == 'POST':
            is_valid = value not in self.list_set

        if not is_valid:
            raise ValidationError(self.get_error_message())

        return True


class ModelUniqueValidator(Validator):
    message = 'Choose another %(title)s'
    def __init__(self, bundle, title, field, *args, **kwargs):
        super(ModelUniqueValidator, self).__init__(bundle, title, *args, **kwargs)
        self.field = field
        # TODO: more fields so we can validate more than one field at once

    def validate(self, value):
        is_valid = True

        # build kwargs
        kwargs = {
            self.field: getattr(self.bundle.obj, self.field)
        }

        if not self.kwargs.get('case_sensitive', False):
            kwargs = {
                '%s__iexact' % self.field : getattr(self.bundle.obj, self.field)
            }

        list_set = self.bundle.obj.__class__._default_manager.filter(Q(**kwargs))

        if self.bundle.obj.pk:
            list_set = list_set.filter(~Q(pk=self.bundle.obj.pk))

        is_valid = not list_set.exists()

        if not is_valid:
            raise ValidationError(self.get_error_message())

        return True