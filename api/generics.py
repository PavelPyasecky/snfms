from rest_framework import generics
from rest_framework.viewsets import ModelViewSet

from api import mixins


class NoCacheModelViewSet(ModelViewSet):
    def list(self, request, *args, **kwargs):
        resp = super(NoCacheModelViewSet, self).list(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp

    def retrieve(self, request, *args, **kwargs):
        resp = super(NoCacheModelViewSet, self).retrieve(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheListCreateAPIView(mixins.LongListModelMixin, generics.ListCreateAPIView):
    def list(self, request, *args, **kwargs):
        resp = super(NoCacheListCreateAPIView, self).list(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheListAPIView(mixins.LongListModelMixin, generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        resp = super(NoCacheListAPIView, self).list(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheRetrieveUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    def retrieve(self, request, *args, **kwargs):
        resp = super(NoCacheRetrieveUpdateDeleteAPIView, self).retrieve(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    def retrieve(self, request, *args, **kwargs):
        resp = super(NoCacheRetrieveUpdateAPIView, self).retrieve(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheRetrieveCreateAPIView(generics.RetrieveAPIView, generics.CreateAPIView):
    def retrieve(self, request, *args, **kwargs):
        resp = super(NoCacheRetrieveCreateAPIView, self).retrieve(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheRetrieveAPIView(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        resp = super(NoCacheRetrieveAPIView, self).retrieve(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheRetrieveDeleteAPIView(generics.RetrieveDestroyAPIView):
    def retrieve(self, request, *args, **kwargs):
        resp = super(NoCacheRetrieveDeleteAPIView, self).retrieve(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheRetrieveCreateDestroyAPIView(NoCacheRetrieveCreateAPIView, generics.DestroyAPIView):
    pass


class NoCacheRetrieveCreateUpdateDestroyAPIView(NoCacheRetrieveUpdateDeleteAPIView, generics.CreateAPIView):
    pass
