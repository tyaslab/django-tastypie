from django.core.urlresolvers import resolve
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import get_script_prefix, Resolver404
from django.db.models import get_model

from tastypie.resources import ModelResource
from tastypie.exceptions import NotFound

class PolymorphicModelResource(ModelResource):
    class Meta:
        polymorphic_querystring = 'model'
        polymorphic_resources = {}

    def get_polymorphic_resource(self, key):
        return self._meta.polymorphic_resources[key](api_name=self._meta.api_name)

    def full_dehydrate(self, bundle, for_list=False):
        """
        dehydrate from the real model of polymorphic
        add 'model' element to identify the real model
        """
        real_instance_model = bundle.obj.get_real_instance_class()
        real_instance_name = real_instance_model.__name__
        real_instance_module_string = '%s.%s' % (real_instance_model._meta.app_label, real_instance_name)

        is_parent_model = real_instance_model == self._meta.object_class

        if not is_parent_model:
            polymorphic_resource = self.get_polymorphic_resource(real_instance_module_string)

            if bundle.obj is None:
                bundle.obj = real_instance_model()

            self.fields = polymorphic_resource.fields
            self._meta.resource_name = polymorphic_resource._meta.resource_name

        bundle.data['model'] = real_instance_module_string

        return super(PolymorphicModelResource, self).full_dehydrate(bundle, for_list=for_list)

    def obj_create(self, bundle, **kwargs):
        """
        based on polymorphic_querystring, create a model
        """
        model_qs = bundle.request.GET.get(self._meta.polymorphic_querystring, None)
        object_class = None
        if model_qs is not None:
            real_instance_module_string = model_qs
            real_instance_model = get_model(real_instance_module_string)
            real_instance_name = real_instance_model.__name__

            is_parent_model = real_instance_model == self._meta.object_class
            if not is_parent_model:
                polymorphic_resource = self.get_polymorphic_resource(real_instance_module_string)

                object_class = real_instance_model

                self.fields = polymorphic_resource.fields
                self._meta.resource_name = polymorphic_resource._meta.resource_name

        return super(PolymorphicModelResource, self).obj_create(bundle, object_class=object_class, **kwargs)

    def get_via_uri(self, uri, request=None):
        """
        so the real resource has the real uri
        """
        resolved_uri = resolve(uri)
        detail_uri_name = resolved_uri.kwargs[self._meta.detail_uri_name]

        uri_kwargs = self.resource_uri_kwargs()
        uri_kwargs[self._meta.detail_uri_name] = detail_uri_name
        uri = self._build_reverse_url('api_dispatch_detail', kwargs=uri_kwargs)

        return super(PolymorphicModelResource, self).get_via_uri(uri, request=request)