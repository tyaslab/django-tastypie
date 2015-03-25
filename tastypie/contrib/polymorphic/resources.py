from tastypie.resources import ModelResource
from tastypie.utils import dict_strip_unicode_keys
from django.utils.importlib import import_module

def load_variable(module_path):
    module_bits = module_path.split('.')
    module_path, the_variable = '.'.join(module_bits[:-1]), module_bits[-1]

    i = import_module(module_path)
    variable = getattr(i, the_variable)

    return variable


class PolymorphicModelResourceMixin(object):
    '''
    # How to create Resource for PolymorphicModel
    1. Create BaseResource
    2. Create A Resource of the topmost model and add polymorphic_resource in Meta model

    class BaseMyResource(PolymorphicModelResourceMixin, AnyBaseResource):
        # ... any resource fields


    class MyResource(BaseMyResource):
        class Meta(BaseMyResource.Meta):
            queryset = MyModel.objects.all()
            resource_name = 'myresource'
            polymorphic_resource = {
                # ... the submodels....
                Land: 'doniclub.resources.LandResource',
                Building: 'doniclub.resources.BuildingResource',
                Car: 'doniclub.resources.CarResource',
                Fashion: 'doniclub.resources.FashionResource',
                PhoneNumber: 'doniclub.resources.PhoneNumberResource'
            }

    Or... if you don't want to mixin, you can use PolymorphicModelResource
    '''
    def build_filters(self, filters=None):
        if filters is not None:
            filters = dict_strip_unicode_keys(filters)

            applicable_filters = []

            for key, content_list in self._meta.filtering.items():
                if isinstance(content_list, list):
                    for content in content_list:
                        applicable_filters.append('%s__%s' % (key, content))
                        if content == 'exact':
                            applicable_filters.append(key)

            new_filters = {}
            for key in filters.keys():
                if key in applicable_filters:
                    new_filters.update({
                        key: filters[key]
                    })

            filters = new_filters.copy()

            return filters

        return super(PolymorphicModelResourceMixin, self).build_filters(filters=filters)

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

