from ruamel.yaml import YAML as ruamel_YAML
from ruamel.yaml.compat import StringIO


# https://yaml.readthedocs.io/en/latest/example.html#output-of-dump-as-a-string
class YAML(ruamel_YAML):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.width = 4000
        self.default_flow_style = False

    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        ruamel_YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()
