from tastypie.resources import ModelResource
from django.utils.importlib import import_module

def load_variable(module_path):
    module_bits = module_path.split('.')
    module_path, the_variable = '.'.join(module_bits[:-1]), module_bits[-1]

    i = import_module(module_path)
    variable = getattr(i, the_variable)

    return variable


class PolymorphicModelResourceMixin(object):
    def get_polymorphic_resource(self, bundle):
        if type(bundle.obj) == self._meta.object_class:
            return self

        resource_string = self._meta.polymorphic_resource[type(bundle.obj)]

        return load_variable(resource_string)()

    def full_dehydrate(self, bundle, for_list=False):
        resource = self.get_polymorphic_resource(bundle)

        if resource == self:
            return super(PolymorphicModelResourceMixin, self).full_dehydrate(bundle, for_list=for_list)

        return resource.full_dehydrate(bundle, for_list=for_list)

    def dehydrate_resource_uri(self, bundle):
        resource = self.get_polymorphic_resource(bundle)

        if resource == self:
            return super(PolymorphicModelResourceMixin, self).dehydrate_resource_uri(bundle)

        return resource.dehydrate_resource_uri(bundle)

class PolymorphicModelResource(PolymorphicModelResourceMixin, ModelResource):
    pass