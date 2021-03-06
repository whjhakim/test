#   The class of the get test data job unit


from common.util import get_class_func_name
from event_framework.job_unit import JobUnit


__author__ = 'chenxin'    
__date__ = '2017-4-9'  
__version__ = 1.0



class GetTestDataJob(JobUnit):
    
    def __init__(self, task_unit, job_n, **params):
        
        '''
        params:
            task_unit: the task unit instance this job unit belongs to
            job_n: the name of this job given in the job unit sequence
            params: other parameters may used for extension
        '''
        super(GetTestDataJob, self).__init__(task_unit, job_n, **params)

    def execute_job(self, **params):

        '''
        called by the task unit to start the execution of this job.
        derived job unit class should override this method to deploy own processing logic

        '''
        try:
            event = self.task_unit.get_triggered_event()
            ctx_ns = event.get_event_data()['context_namespace']
            ctx_store = self.task_unit.task_scheduler.context_store
            ctx_handlers = ctx_store.get_context_namespace_process_handler(ctx_ns)
            r_data = []
            for h in ctx_handlers:
                r_data.append(h.get_context_item())
                h.process_finish()
            event.set_return_data_asyn(r_data)
            self._output_params(para_1='1', para_2='2')
            self._execution_finish()
        except Exception, e:
            print Exception, ':', e, \
                      ' in %s:%s' % get_class_func_name(self)
