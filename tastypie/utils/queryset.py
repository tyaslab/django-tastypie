from django.db.models import Q

def fuzzy_filter(queryset, fields, query):
    query = '.*%s.*' % '.*'.join(list(query))

    the_q = Q()
    if not isinstance(fields, list):
        fields = [fields]

    for field in fields:
        the_q = the_q | Q(**{'%s__iregex' % field : query})

    return queryset.filter(the_q)