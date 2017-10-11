import inspect
import json

import jinja2

import requests
from service.views import VideoizeService


def is_defined_method(cls):
    return inspect.getmembers(cls, predicate=lambda m: inspect.ismethod(m) and m.__func__ in m.im_class.__dict__.values())


def list_public_method(cls):
    for method_name, _ in is_defined_method(cls):
        if method_name[0] == "_":
            continue

        method = getattr(cls, method_name)
        argspec = inspect.getargspec(method)
        yield method_name, argspec


template = """
from ggrpc import RPCClient

class {{cls_name}}(RPCClient):
    {% for method, arg in methods %}
    {% if arg %}
    def {{method}}(self, {{arg}}):
    {% else %}
    def {{method}}(self):
    {% endif %}
        return self._call("{{method}}", {{arg}})
    {% endfor %}
"""


def client_factory(kls):
    # TODO: add func doc in the future
    methods = []
    for name, argspec in list_public_method(kls):
        args = list(argspec.args[1:])

        if argspec.defaults:
            for k in range(len(argspec.defaults)):
                idx = -1 - k
                assert isinstance(argspec.defaults[idx], (basestring, int, float))

                if isinstance(argspec.defaults[idx], basestring):
                    args[idx] = "%s='%s'" % (args[idx], argspec.defaults[idx])
                else:
                    args[idx] = "%s=%s" % (args[idx], argspec.defaults[idx])

        if argspec.varargs:
            args.append("*args")

        if argspec.keywords:
            args.append("**kwargs")

        methods.append((name, ", ".join(args)))

    return jinja2.Template(template).render(cls_name=kls.__name__, methods=methods)


class RPCClient(object):
    def __init__(self, base_uri):
        self.base_uri = base_uri

    def _call(self, name, *args, **kwargs):
        requests.post(self.base_uri + name, {
            "params": json.dumps({
                "args": args,
                "kwargs": kwargs
            })
        })
