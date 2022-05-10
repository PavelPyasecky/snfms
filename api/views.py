from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView


def clean_reverse(name, *args, **kwargs):
    return reverse(name, *args, **kwargs).replace('%3A', ':')


class APIIndex(APIView):

    def get(self, request, *args, **kwargs):
        return Response({
            "Books information and settings": {
                "description": "Book organization, attributes, and configuration",
                "url": clean_reverse("account_index", request=request)
            },
        })
