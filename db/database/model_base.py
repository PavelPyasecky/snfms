from typing import List

from django.db import models


class SchemaModel(models.Model):

    @classmethod
    def _get_model_field_names(cls) -> List[str]:
        return [f.name for f in cls._meta.fields]

    class Meta:
        abstract = True
        ordering = ['pk']
