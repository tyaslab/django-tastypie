from django.core.urlresolvers import resolve
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import get_script_prefix, Resolver404
from django.db.models import get_model

from tastypie.bundle import Bundle
from tastypie.resources import ModelResource
from tastypie.exceptions import NotFound


class PolymorphicModelResource(ModelResource):
    class Meta:
        polymorphic_resources = {}

    def get_polymorphic_resource(self, key):
        return self._meta.polymorphic_resources[key]

    def full_dehydrate(self, bundle, for_list=False):
        real_model = bundle.obj.get_real_instance_class()
        key = '%s.%s' % (real_model._meta.app_label, real_model.__name__)

        is_parent_model = real_model == self._meta.object_class

        if not is_parent_model:
            polymorphic_resource = self.get_polymorphic_resource(key)

            if bundle.obj is None:
                bundle.obj = real_model()

            # set fields to appropriate resource
            # but keep the original information so the original class still in use
            # useful when for_list = True
            self.original_fields = getattr(self, 'original_fields', self.fields)
            self.original_resource_name = getattr(self, 'original_resource_name', self._meta.resource_name)

            self.fields = polymorphic_resource.fields
            self._meta.resource_name = polymorphic_resource._meta.resource_name
        else:
            self.fields = getattr(self, 'original_fields', self.fields)
            self._meta.resource_name = getattr(self, 'original_resource_name', self._meta.resource_name)

        return super(PolymorphicModelResource, self).full_dehydrate(bundle, for_list=for_list)