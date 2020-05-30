from django.core.serializers import serialize
from django.shortcuts import render
from django.http import HttpResponse, Http404
from rest_framework import generics

from geocontext.forms import GeoContextForm
from geocontext.models.csr import ContextServiceRegistry
from geocontext.models.utilities import CSRUtils, retrieve_external_csr, UtilArg
from geocontext.serializers.csr import CSRSerializer


class CSRListAPIView(generics.ListAPIView):
    """List all context service registry."""
    queryset = ContextServiceRegistry.objects.all()
    serializer_class = CSRSerializer


class CSRDetailAPIView(generics.RetrieveAPIView):
    """Retrieve a detail of a context service registry."""

    lookup_field = 'key'

    queryset = ContextServiceRegistry.objects.all()
    serializer_class = CSRSerializer


def get_context(request):
    """Get context view."""
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = GeoContextForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            cleaned_data = form.cleaned_data
            x = cleaned_data['x']
            y = cleaned_data['y']
            srid = cleaned_data.get('srid', 4326)
            service_registry_key = cleaned_data['service_registry_key']
            csr_util = CSRUtils(service_registry_key, x, y, srid)
            cache = csr_util.retrieve_cache()
            if cache is None:
                util_arg = UtilArg(group_key=None, csr_util=csr_util)
                new_util_arg = retrieve_external_csr(util_arg)
                if new_util_arg is not None:
                    cache = new_util_arg.csr_util.create_cache()
            fields = ('value', 'key')
            if cache:
                return HttpResponse(
                    serialize(
                        'geojson',
                        [cache],
                        geometry_field='geometry_multi_polygon',
                        fields=fields),
                    content_type='application/json')
            else:
                raise Http404(
                    'Sorry! We could not find context for your point!')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = GeoContextForm(initial={'srid': 4326})

    return render(request, 'geocontext/get_context.html', {'form': form})