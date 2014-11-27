from __future__ import unicode_literals
from tastypie.exceptions import TastypieError, Unauthorized


class Authorization(object):
    """
    A base class that provides no permissions checking.
    """
    def __get__(self, instance, owner):
        """
        Makes ``Authorization`` a descriptor of ``ResourceOptions`` and creates
        a reference to the ``ResourceOptions`` object that may be used by
        methods of ``Authorization``.
        """
        self.resource_meta = instance
        return self

    def apply_limits(self, request, object_list):
        """
        Deprecated.

        FIXME: REMOVE BEFORE 1.0
        """
        raise TastypieError("Authorization classes no longer support `apply_limits`. Please update to using `read_list`.")

    def read_list(self, object_list, bundle):
        """
        Returns a list of all the objects a user is allowed to read.

        Should return an empty list if none are allowed.

        Returns the entire list by default.
        """
        return object_list

    def read_detail(self, object_list, bundle):
        """
        Returns either ``True`` if the user is allowed to read the object in
        question or throw ``Unauthorized`` if they are not.

        Returns ``True`` by default.
        """
        return True

    def create_list(self, object_list, bundle):
        """
        Unimplemented, as Tastypie never creates entire new lists, but
        present for consistency & possible extension.
        """
        raise NotImplementedError("Tastypie has no way to determine if all objects should be allowed to be created.")

    def create_detail(self, object_list, bundle):
        """
        Returns either ``True`` if the user is allowed to create the object in
        question or throw ``Unauthorized`` if they are not.

        Returns ``True`` by default.
        """
        return True

    def update_list(self, object_list, bundle):
        """
        Returns a list of all the objects a user is allowed to update.

        Should return an empty list if none are allowed.

        Returns the entire list by default.
        """
        return object_list

    def update_detail(self, object_list, bundle):
        """
        Returns either ``True`` if the user is allowed to update the object in
        question or throw ``Unauthorized`` if they are not.

        Returns ``True`` by default.
        """
        return True

    def delete_list(self, object_list, bundle):
        """
        Returns a list of all the objects a user is allowed to delete.

        Should return an empty list if none are allowed.

        Returns the entire list by default.
        """
        return object_list

    def delete_detail(self, object_list, bundle):
        """
        Returns either ``True`` if the user is allowed to delete the object in
        question or throw ``Unauthorized`` if they are not.

        Returns ``True`` by default.
        """
        return True


class ReadOnlyAuthorization(Authorization):
    """
    Default Authentication class for ``Resource`` objects.

    Only allows ``GET`` requests.
    """
    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        return []

    def create_detail(self, object_list, bundle):
        raise Unauthorized("You are not allowed to access that resource.")

    def update_list(self, object_list, bundle):
        return []

    def update_detail(self, object_list, bundle):
        raise Unauthorized("You are not allowed to access that resource.")

    def delete_list(self, object_list, bundle):
        return []

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("You are not allowed to access that resource.")


class DjangoAuthorization(Authorization):
    """
    Uses permission checking from ``django.contrib.auth`` to map
    ``POST / PUT / DELETE / PATCH`` to their equivalent Django auth
    permissions.

    Both the list & detail variants simply check the model they're based
    on, as that's all the more granular Django's permission setup gets.
    """
    def base_checks(self, request, model_klass):
        # If it doesn't look like a model, we can't check permissions.
        if not model_klass or not getattr(model_klass, '_meta', None):
            return False

        # User must be logged in to check permissions.
        if not hasattr(request, 'user'):
            return False

        return model_klass

    def read_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        # GET-style methods are always allowed.
        return object_list

    def read_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        # GET-style methods are always allowed.
        return True

    def create_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        permission = '%s.add_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            return []

        return object_list

    def create_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.add_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def update_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        permission = '%s.change_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            return []

        return object_list

    def update_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.change_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def delete_list(self, object_list, bundle):
        klass = self.base_checks(bundle.request, object_list.model)

        if klass is False:
            return []

        permission = '%s.delete_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            return []

        return object_list

    def delete_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)

        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")

        permission = '%s.delete_%s' % (klass._meta.app_label, klass._meta.module_name)

        if not bundle.request.user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True


class CheckAuthorityMixin(object):
    def check_authority(self, object_list, bundle):
        return True

    def check_list_authority(self, object_list, bundle):
        return True

    def check_detail_authority(self, object_list, bundle):
        return True

    def check_read_authority(self, object_list, bundle):
        return True

    def check_create_authority(self, object_list, bundle):
        return True

    def check_update_authority(self, object_list, bundle):
        return True

    def check_delete_authority(self, object_list, bundle):
        return True

    def check_read_list_authority(self, object_list, bundle):
        return True

    def check_read_detail_authority(self, object_list, bundle):
        return True

    def check_create_list_authority(self, object_list, bundle):
        return True

    def check_create_detail_authority(self, object_list, bundle):
        return True

    def check_update_list_authority(self, object_list, bundle):
        return True

    def check_update_detail_authority(self, object_list, bundle):
        return True

    def check_delete_list_authority(self, object_list, bundle):
        return True

    def check_delete_detail_authority(self, object_list, bundle):
        return True


class Authorization(Authorization, CheckAuthorityMixin):
    def __init__(self, *args, **kwargs):
        crud_list = ['create', 'read', 'update', 'delete']
        ld_list = ['list', 'detail']
        for crud in crud_list:
            for ld in ld_list:
                auth_check = '%s_%s_authorized' % (crud, ld)

                check_value = False
                if kwargs.has_key('all'):
                    check_value = kwargs.get('all', False)
                elif kwargs.has_key(ld):
                    check_value = kwargs.get(ld, False)
                elif kwargs.has_key(crud):
                    check_value = kwargs.get(crud, False)
                elif kwargs.has_key(auth_check):
                    check_value = kwargs.get(auth_check, False)

                setattr(self, auth_check, check_value)

    def read_list(self, object_list, bundle):
        self.check_authority(object_list, bundle)
        self.check_list_authority(object_list, bundle)
        self.check_read_authority(object_list, bundle)
        self.check_read_list_authority(object_list, bundle)

        if not self.read_list_authorized:
            raise Unauthorized("You are not allowed to access that resource.")

        return object_list

    def read_detail(self, object_list, bundle):
        self.check_authority(object_list, bundle)
        self.check_detail_authority(object_list, bundle)
        self.check_read_authority(object_list, bundle)
        self.check_read_detail_authority(object_list, bundle)

        if not self.read_detail_authorized:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def create_list(self, object_list, bundle):
        self.check_authority(object_list, bundle)
        self.check_list_authority(object_list, bundle)
        self.check_create_authority(object_list, bundle)
        self.check_create_list_authority(object_list, bundle)

        if not self.create_list_authorized:
            raise Unauthorized("You are not allowed to access that resource.")

        return object_list

    def create_detail(self, object_list, bundle):
        self.check_authority(object_list, bundle)
        self.check_detail_authority(object_list, bundle)
        self.check_create_authority(object_list, bundle)
        self.check_create_detail_authority(object_list, bundle)

        if not self.create_detail_authorized:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def update_list(self, object_list, bundle):
        self.check_authority(object_list, bundle)
        self.check_list_authority(object_list, bundle)
        self.check_update_authority(object_list, bundle)
        self.check_update_list_authority(object_list, bundle)

        if not self.update_list_authorized:
            raise Unauthorized("You are not allowed to access that resource.")

        return object_list

    def update_detail(self, object_list, bundle):
        self.check_authority(object_list, bundle)
        self.check_detail_authority(object_list, bundle)
        self.check_update_authority(object_list, bundle)
        self.check_update_detail_authority(object_list, bundle)

        if not self.update_detail_authorized:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def delete_list(self, object_list, bundle):
        self.check_authority(object_list, bundle)
        self.check_list_authority(object_list, bundle)
        self.check_delete_authority(object_list, bundle)
        self.check_delete_list_authority(object_list, bundle)

        if not self.delete_list_authorized:
            raise Unauthorized("You are not allowed to access that resource.")

        return object_list

    def delete_detail(self, object_list, bundle):
        self.check_authority(object_list, bundle)
        self.check_detail_authority(object_list, bundle)
        self.check_delete_authority(object_list, bundle)
        self.check_delete_detail_authority(object_list, bundle)

        if not self.delete_detail_authorized:
            raise Unauthorized("You are not allowed to access that resource.")

        return True


class AuthenticatedAuthorization(Authorization):
    def check_authority(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized("You are not allowed to access that resource.")

        return super(AuthenticatedAuthorization, self).check_authority(object_list, bundle)


class StaffAuthorization(Authorization):
    def check_authority(self, object_list, bundle):
        if not bundle.request.user.is_staff:
            raise Unauthorized("You are not allowed to access that resource.")

        return super(StaffAuthorization, self).check_authority(object_list, bundle)


class SuperUserAuthorization(Authorization):
    def check_authority(self, object_list, bundle):
        if not bundle.request.user.is_superuser():
            raise Unauthorized("You are not allowed to access that resource.")

        return super(SuperUserAuthorization, self).check_authority(object_list, bundle)


class MultipleAuthorization(Authorization):
    def __init__(self, *args, **kwargs):
        super(MultipleAuthorization, self).__init__(all=True)

        self.auth_classes = []

        if kwargs.get('include_django_auth', True):
            self.auth_classes.append(DjangoAuthorization())

        self.auth_classes = []
        self.auth_classes += args

    def check_read_list_authority(self, object_list, bundle):
        auth_check = False
        for ac in self.auth_classes:
            try:
                object_list = ac.read_list(object_list, bundle)
                auth_check = True
            except Unauthorized:
                pass

        if not auth_check:
            raise Unauthorized("You are not allowed to access that resource.")
        
        return True

    def check_read_detail_authority(self, object_list, bundle):
        auth_check = False
        for ac in self.auth_classes:
            try:
                object_list = ac.read_detail(object_list, bundle)
                auth_check = True
            except Unauthorized:
                pass

        if not auth_check:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def check_create_list_authority(self, object_list, bundle):
        auth_check = False
        for ac in self.auth_classes:
            try:
                object_list = ac.create_list(object_list, bundle)
                auth_check = True
            except Unauthorized:
                pass

        if not auth_check:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def check_create_detail_authority(self, object_list, bundle):
        auth_check = False
        for ac in self.auth_classes:
            try:
                object_list = ac.create_detail(object_list, bundle)
                auth_check = True
            except Unauthorized:
                pass

        if not auth_check:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def check_update_list_authority(self, object_list, bundle):
        auth_check = False
        for ac in self.auth_classes:
            try:
                object_list = ac.update_list(object_list, bundle)
                auth_check = True
            except Unauthorized:
                pass

        if not auth_check:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def check_update_detail_authority(self, object_list, bundle):
        auth_check = False
        for ac in self.auth_classes:
            try:
                object_list = ac.update_detail(object_list, bundle)
                auth_check = True
            except Unauthorized:
                pass

        if not auth_check:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def check_delete_list_authority(self, object_list, bundle):
        auth_check = False
        for ac in self.auth_classes:
            try:
                object_list = ac.delete_list(object_list, bundle)
                auth_check = True
            except Unauthorized:
                pass

        if not auth_check:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def check_delete_detail_authority(self, object_list, bundle):
        auth_check = False
        for ac in self.auth_classes:
            try:
                object_list = ac.delete_detail(object_list, bundle)
                auth_check = True
            except Unauthorized:
                pass

        if not auth_check:
            raise Unauthorized("You are not allowed to access that resource.")

        return True


class AnonymousReadOnlyAuthorization(MultipleAuthorization):
    def __init__(self, *args):
        super(AnonymousReadOnlyAuthorization, self).__init__(
            Authorization(read=True),
            StaffAuthorization(all=True)
        )


# JUST FOR ModelResource
class AuthorOnlyAuthorization(Authorization):
    def __init__(self, author_field, *args, **kwargs):
        super(AuthorOnlyAuthorization, self).__init__(*args, **kwargs)
        self.author_field = author_field

    def check_detail_authority(self, object_list, bundle):
        check = bundle.request.user.is_authenticated() and ((getattr(bundle.obj, self.author_field) is not None and bundle.request.user.pk == getattr(bundle.obj, self.author_field).pk) or bundle.obj.author is None)
        if not check:
            raise Unauthorized("You are not allowed to access that resource.")

        return True


class UserModelAuthorization(Authorization):
    def check_detail_authority(self, object_list, bundle):
        try:
            check = bundle.request.user.pk == bundle.obj.pk
        except:
            check = False

        if not check:
            raise Unauthorized("You are not allowed to access that resource.")

        return True

