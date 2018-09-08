from functools import wraps
from typing import *
from uuid import uuid4 as uuid

import observable

from pros.common import logger

_uuid_table = dict()  # type: Dict[str, Observable]


class Observable(observable.Observable):
    @classmethod
    def notify(cls, uuid, event, *args, **kwargs):
        if isinstance(uuid, Observable):
            uuid = uuid.uuid
        if uuid in _uuid_table:
            _uuid_table[uuid].trigger(event, *args, **kwargs)
        else:
            logger(__name__).warning(f'Could not find an Observable to notify with UUID: {uuid}', sentry=True)

    def on(self, event, *handlers,
           bound_args: Tuple[Any, ...] = None, bound_kwargs: Dict[str, Any] = None,
           asynchronous: bool = False) -> Callable:
        if bound_args is None:
            bound_args = []
        if bound_kwargs is None:
            bound_kwargs = {}

        if asynchronous:
            def bind(h):
                def bound(*args, **kw):
                    from threading import Thread
                    from pros.common.utils import with_click_context
                    t = Thread(target=with_click_context(h), args=(*bound_args, *args), kwargs={**bound_kwargs, **kw})
                    t.start()
                    return t

                return bound
        else:
            def bind(h):
                @wraps(h)
                def bound(*args, **kw):
                    return h(*bound_args, *args, **bound_kwargs, **kw)

                return bound

        return super(Observable, self).on(event, *[bind(h) for h in handlers])

    def trigger(self, event, *args, **kw):
        logger(__name__).debug(f'Triggered {self} "{event}" event: {args} {kw}')
        return super().trigger(event, *args, **kw)

    def __init__(self):
        self.uuid = str(uuid())
        _uuid_table[self.uuid] = self
        super(Observable, self).__init__()
