from django.core.urlresolvers import resolve
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import get_script_prefix, Resolver404
from django.db.models import get_model

from tastypie.bundle import Bundle
from tastypie.resources import ModelResource
from tastypie.exceptions import NotFound


class PolymorphicModelResourceMixin(object):
    class Meta:
        polymorphic_resources = {}

    def get_polymorphic_resource(self, key):
        return self._meta.polymorphic_resources[key]

    def get_object_list(self, request, queryset=None):
        # I don't know why I should do it
        # But what I know is, when I replace with this, everything runs smoothly
        # Problem?

        queryset = self._meta.object_class.objects.all()

        return super(PolymorphicModelResourceMixin, self).get_object_list(request, queryset=queryset)

    def full_dehydrate(self, bundle, for_list=False):
        real_model = bundle.obj.get_real_instance_class()

        is_parent_model = real_model == self._meta.object_class

        if not is_parent_model:
            key = '%s.%s' % (real_model._meta.app_label, real_model.__name__)
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

        return super(PolymorphicModelResourceMixin, self).full_dehydrate(bundle, for_list=for_list)

    def get_via_uri(self, uri, request=None):
        """
        TODO: Must look for the best to it
        """
        resolved_uri = resolve(uri)
        detail_uri_name = resolved_uri.kwargs[self._meta.detail_uri_name]

        uri_kwargs = self.resource_uri_kwargs()
        uri_kwargs[self._meta.detail_uri_name] = detail_uri_name
        uri = self._build_reverse_url('api_dispatch_detail', kwargs=uri_kwargs)

        return super(PolymorphicModelResourceMixin, self).get_via_uri(uri, request=request)

    def build_filters(self, filters=None):
        injected_filter = {}
        inject = False
        if filters.get('polymorphic_ctype_id', None):
            inject = True
            injected_filter = {
                'polymorphic_ctype_id': filters['polymorphic_ctype_id']
            }

        filters = super(PolymorphicModelResourceMixin, self).build_filters(filters=filters)

        if inject:
            filters.update(injected_filter)

        return filters

class PolymorphicModelResource(PolymorphicModelResourceMixin, ModelResource):
    class Meta(PolymorphicModelResourceMixin.Meta):
        pass