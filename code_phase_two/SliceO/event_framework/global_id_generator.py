#   The class of the global id generator

from common.util import get_class_func_name
from uuid import uuid3, uuid1, NAMESPACE_URL as NS
from threading import currentThread as get_thread, Lock as lock

CODE = 'utf-8'

NAMESPACE_EVENT = 'event'
NAMESPACE_EVENT_LISTENER = 'event_listener'
NAMESPACE_TASK = 'task'
NAMESPACE_CONTEXT_ITEM = 'context_item'

__author__ = 'chenxin'    
__date__ = '2017-3-31'  
__version__ = 1.0

class GlobalIdGenerator(object):
    
    def __init__(self):
        pass
        self.dynamic_namespace = {}
        self.mutex = lock()

    def _get_id(self, ns, *params):
        
        '''
        generate a guid
        params:
            ns: a namespace indicating the id type
            params: input parameters to generate id 
        '''
        try:
            env = (str(get_thread().ident) + '-' + str(uuid1())).encode(CODE)
            return str(uuid3(NS, '_'.join([ns, env] + map(str, params)).encode(CODE))).encode(CODE)
        except Exception, e:
            print Exception, ':', e, \
                      ' in %s:%s' % get_class_func_name(self)
            return

    def _get_id_without_env(self, ns, *params):
        
        '''
        generate a guid without the environment parameters
        params:
            ns: a namespace indicating the id type
            params: input parameters to generate id 
        '''
        try:
            return str(uuid3(NS, '_'.join([ns] + map(str, params)).encode(CODE))).encode(CODE)
        except Exception, e:
            print Exception, ':', e, \
                      ' in %s:%s' % get_class_func_name(self)
            return
    
    def add_dynamic_namespace(self, ns, ns_short):

        '''
        add a dynamic namespace for id generation
        params:
            ns: the namespace to be added
            ns_short: a short name of the namespace for index
        '''
        if self.mutex.acquire():
            self.dynamic_namespace[ns_short] = ns
            self.mutex.release()
    
    def get_event_id(self, *params):
        return self._get_id(NAMESPACE_EVENT, *params)

    def get_event_listener_id(self, *params):
        return self._get_id(NAMESPACE_EVENT_LISTENER, *params)

    def get_task_id(self, *params):
        return self._get_id(NAMESPACE_TASK, *params)

    def get_context_item_id(self, *params):
        return self._get_id(NAMESPACE_CONTEXT_ITEM, *params)

    def get_dynamic_namespace_id(self, ns_short, ns=None, *params):
        if self.mutex.acquire():
            if ns:
                return self._get_id(ns, *params)
            else:
                return self._get_id(self.dynamic_namespace[ns_short], *params)
            self.mutex.release()

    def get_event_id_without_env(self, *params):
        return self._get_id_without_env(NAMESPACE_EVENT, *params)

    def get_event_listener_id_without_env(self, *params):
        return self._get_id_without_env(NAMESPACE_EVENT_LISTENER, *params)

    def get_task_id_without_env(self, *params):
        return self._get_id_without_env(NAMESPACE_TASK, *params)

    def get_context_item_id_without_env(self, *params):
        return self._get_id_without_env(NAMESPACE_CONTEXT_ITEM, *params)

    def get_dynamic_namespace_id_without_env(self, ns_short, ns=None, *params):
        if self.mutex.acquire():
            if ns:
                return self._get_id_without_env(ns, *params)
            else:
                return self._get_id_without_env(self.dynamic_namespace[ns_short], *params)
            self.mutex.release()