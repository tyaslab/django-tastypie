import datetime
import re
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from tastypie.exceptions import ApiFieldError
from tastypie.fields import DateField, TimeField, DateTimeField

class Validator(object):
    title = 'input'
    message = 'Please check %(title)s'

    def __init__(self, **kwargs):
        self.title = kwargs.pop('title', self.title)
        self.message = kwargs.pop('message', self.message)

    def get_error_message(self, **kwargs):
        if not kwargs.has_key('title'):
            kwargs['title'] = self.title

        error_message = self.message % kwargs
        error_message = '%s%s' % (error_message[0].upper(), error_message[1:-1])

        return self.message % kwargs

    def validate(self, value, bundle=None, **kwargs):
        raise NotImplementedError

    def return_or_raise(self, is_valid):
        if not is_valid:
            raise ValidationError(self.get_error_message())

        return True


class UniqueValidator(Validator):
    message = 'Choose another %(title)s'

    def __init__(self, **kwargs):
        super(UniqueValidator, self).__init__(**kwargs)
        self.list_set = kwargs.pop('list_set')
        self.case_sensitive = kwargs.pop('case_sensitive', True)

        if not self.case_sensitive:
            self.list_set = [x.lower() for x in self.list_set if isinstance(x, (str, unicode))]

    def validate(self, value, bundle=None, **kwargs):
        if value is None:
            return self.return_or_raise(True)

        is_valid = True

        if not self.case_sensitive and isinstance(value, (str, unicode)):
            value = value.lower()

        if bundle is None or bundle.request.method == 'POST':
            is_valid = value not in self.list_set

        return self.return_or_raise(is_valid)


class MaxLengthValidator(Validator):
    message = 'Max length is %(max_length)s'

    def __init__(self, max_length, **kwargs):
        super(MaxLengthValidator, self).__init__(**kwargs)
        self.max_length = max_length

    def validate(self, value, **kwargs):
        if value is None:
            return self.return_or_raise(True)

        is_valid = len(value) <= self.max_length

        return self.return_or_raise(is_valid)


class MinLengthValidator(Validator):
    message = 'Min length is %(min_length)s'

    def __init__(self, min_length, **kwargs):
        super(MinLengthValidator, self).__init__(**kwargs)
        self.min_length = min_length

    def validate(self, value, **kwargs):
        if value is None:
            return self.return_or_raise(True)

        is_valid = len(value) >= self.min_length

        return self.return_or_raise(is_valid)


class ModelUniqueValidator(Validator):
    message = 'Choose another %(title)s'

    def __init__(self, **kwargs):
        super(ModelUniqueValidator, self).__init__(**kwargs)
        self.case_sensitive = kwargs.pop('case_sensitive', True)
        self.field = kwargs.pop('field')

    def validate(self, value, bundle, **kwargs):
        if value is None:
            return self.return_or_raise(True)

        is_valid = True

        # build kwargs
        kwargs = {
            self.field: getattr(bundle.obj, self.field)
        }

        if not self.case_sensitive:
            kwargs = {
                '%s__iexact' % self.field : getattr(bundle.obj, self.field)
            }

        list_set = bundle.obj.__class__._default_manager.filter(Q(**kwargs))

        # if object already exists, then exlude itself from the list
        if bundle.obj.pk:
            list_set = list_set.filter(~Q(pk=bundle.obj.pk))

        is_valid = not list_set.exists()

        return self.return_or_raise(is_valid)


class RequiredValidator(Validator):
    message = '%(title)s is required'

    def validate(self, value, **kwargs):
        is_valid = value is not None
        return self.return_or_raise(is_valid)


class DateValidator(Validator):
    def validate(self, value, **kwargs):
        try:
            date_field = DateField().convert(value)
            is_valid = True
        except ApiFieldError:
            is_valid = False

        return self.return_or_raise(is_valid)


class TimeValidator(Validator):
    def validate(self, value, **kwargs):
        try:
            date_field = TimeField().convert(value)
            is_valid = True
        except ApiFieldError:
            is_valid = False

        return self.return_or_raise(is_valid)


class DateTimeValidator(Validator):
    def validate(self, value, **kwargs):
        try:
            date_field = DateTimeField().convert(value)
            is_valid = True
        except ApiFieldError:
            is_valid = False

        return self.return_or_raise(is_valid)


class AgeValidator(Validator):
    title = 'age'
    message = '%(title)s must be as minimal as %(age)s'

    def __init__(self, **kwargs):
        super(AgeValidator, self).__init__(**kwargs)
        self.age = kwargs.pop('age')

    def validate(self, value, **kwargs):
        if value is None:
            return self.return_or_raise(True)

        if isinstance(value, (str, unicode)):
            value = DateField().convert(value)

        now = timezone.now()
        years_ago = now.replace(year=now.year-self.age)

        is_valid = value <= years_ago

        return self.return_or_raise(is_valid)

    def get_error_message(self, **kwargs):
        return super(AgeValidator, self).get_error_message(age=self.age)


class ChoiceValidator(Validator):
    message = '%(title)s is not a valid choice'
    def __init__(self, **kwargs):
        super(ChoiceValidator, self).__init__(**kwargs)
        self.case_sensitive = kwargs.pop('case_sensitive', True)
        self.choices = kwargs.pop('choices')

    def validate(self, value, **kwargs):
        if value is None:
            return self.return_or_raise(True)

        if not self.case_sensitive and isinstance(value, (str, unicode)):
            value = value.lower()

        is_valid = value in self.choices

        return self.return_or_raise(is_valid)


class RegexValidator(Validator):
    message = '%(title)s does not match pattern'
    pattern = None

    def __init__(self, **kwargs):
        super(RegexValidator, self).__init__(**kwargs)
        self.pattern = kwargs.pop('pattern', self.pattern)

    def validate(self, value, **kwargs):
        if value is None or value == '':
            return self.return_or_raise(True)

        if not isinstance(value, (str, unicode)):
            value = str(value)

        p = re.compile(self.pattern)
        m = p.match(value)

        is_valid = bool(m)

        return self.return_or_raise(is_valid)


class EmailValidator(RegexValidator):
    title = 'email'
    message = 'Enter a valid %(title)s address'
    pattern = r'[a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9_\-\.]+'


class NumberValidator(RegexValidator):
    title = 'number'

    def __init__(self, **kwargs):
        super(NumberValidator, self).__init__(**kwargs)
        self.pattern = r'^(\-|\+)?[0-9]+$'


class DecimalValidator(RegexValidator):
    def __init__(self, **kwargs):
        super(DecimalValidator, self).__init__(**kwargs)
        self.pattern = r'^(\-|\+)?[0-9]+(\.?[0-9]+)?$'


class PhoneNumberValidator(RegexValidator):
    title = 'phone number'
    pattern = r'^\+?[0-9\-\s]+$'


class HexValidator(RegexValidator):
    title = 'hex'
    pattern = r'^[a-fA-F0-9]+$'