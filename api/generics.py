from rest_framework import generics, mixins


class NoCacheListAPIView(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        resp = super(NoCacheListAPIView, self).list(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheListCreateAPIView(generics.ListCreateAPIView):
    def list(self, request, *args, **kwargs):
        resp = super(NoCacheListCreateAPIView, self).list(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp


class NoCacheRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    def retrieve(self, request, *args, **kwargs):
        resp = super(NoCacheRetrieveUpdateAPIView, self).retrieve(request, *args, **kwargs)
        resp['Cache-Control'] = 'no-cache'
        return resp
