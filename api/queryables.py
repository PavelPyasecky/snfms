class Queryable:
    def qs(self, model):
        return model.objects.using(self.customer_domain)

    def create_object(self, model, **kwargs):
        return self.qs(model).create(**kwargs)


class CustomerQueryable(Queryable):
    def __init__(self, customer_domain):
        self.customer_domain = customer_domain


class ControllerQueryable(Queryable):
    customer_domain = 'controller'
