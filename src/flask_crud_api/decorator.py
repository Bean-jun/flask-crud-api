class Swagger:

    Key = "_swagger"

    def __init__(
        self,
        tags=None,
        summary=None,
        deprecated=False,
        description=None,
        parameters=None,
    ):
        self.tags = tags
        self.summary = summary
        self.deprecated = deprecated
        self.description = description
        self.parameters = parameters or []

    def __call__(self, f):
        setattr(f, self.Key, self)
        return f
