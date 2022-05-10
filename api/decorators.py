from functools import wraps


def stored_property(method):
    """
    Property value is computed and stored as object attribute the first time it is used.
    This provides fast access to the property avoiding the same computation over and over again.
    The attribute name to store the property value is generated automatically by adding '_' before the property name.

    Example without and with 'stored_property' decorator:

        import time
        from sfapi.decorators import stored_property


        class SleepProperty(object):
            seconds = 1

            #Imitation of the expensive property
            @property
            def sleep(self):
                time.sleep(self.seconds)
                return self.seconds


        class StoredSleepProperty(object):
            seconds = 1

            #Using '@stored_property' decorator to remember the expensive property
            @stored_property
            def sleep(self):
                time.sleep(self.seconds)
                return self.seconds


        def test_sleep(cls):
            start = time.time()
            sleep = cls()
            for _ in range(100):
                property_value = sleep.sleep

            return time.time() - start


        for cls in (SleepProperty, StoredSleepProperty):
            print('%s elapsed time = %s' % (cls.__name__, test_sleep(cls)))

        Output:
            SleepProperty elapsed time = 100.18659687
            StoredSleepProperty elapsed time = 1.00273180008
    """
    @wraps(method)
    def wrapper(self):
        attr = '_%s' % method.__name__
        if not hasattr(self, attr):
            setattr(self, attr, method(self))

        return getattr(self, attr)

    return property(wrapper)


def stored_method(method):
    """
    The first time the object method is called its return value is stored
    in the dictionary attribute under the key calculated from method's *args and **kwargs.
    This provides fast access to the method return value for any subsequent call with the same set of arguments.
    The attribute name to store the dictionary with method's values is generated automatically by adding '_' before the method name.

    Example without and with 'stored_method' decorator:

        import time
        from sfapi.decorators import stored_method


        class SleepMethod(object):
            #Imitation of the expensive function
            def sleep(self, seconds):
                time.sleep(seconds)
                return seconds


        class StoredSleepMethod(object):
            #Using 'stored_method' decorator to remember the result of the expensive method
            @stored_method
            def sleep(self, seconds):
                time.sleep(seconds)
                return seconds


        def test_sleep(cls):
            start = time.time()
            sleep = cls()
            for _ in range(100):
                method_result = sleep.sleep(1)

            return time.time() - start


        for cls in (SleepMethod, StoredSleepMethod):
            print('%s elapsed time = %s' % (cls.__name__, test_sleep(cls)))

    Output:
        SleepMethod elapsed time = 100.207796097
        StoredSleepMethod elapsed time = 1.00280594826
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        attr = '_%s' % method.__name__
        if not hasattr(self, attr):
            setattr(self, attr, {})

        storage = getattr(self, attr)
        key = (args, tuple(sorted(kwargs.items())))

        if key not in storage:
            storage[key] = method(self, *args, **kwargs)

        return storage[key]

    return wrapper
