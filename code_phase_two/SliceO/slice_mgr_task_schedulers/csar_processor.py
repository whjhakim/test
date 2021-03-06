#   The class of the csar processor task scheduler


import os

from common.util import get_class_func_name, \
                        PROTO_FTP, PROTO_HTTP, \
                        CONTEXT_NAMESPACE_CSAR, EVENT_PRODUCER_LOCAL_REST, \
                        EVENT_TYPE_LOCAL_CSAR_UPLOAD, EVENT_TYPE_CSAR_ONBOARDING, EVENT_TYPE_CSAR_INFO_ACQ, \
                        JOB_SEQ_LOCAL_CSAR_UPLOAD, JOB_SEQ_CSAR_ONBOARDING
from event_framework.task_scheduler import TaskScheduler, INIT_TYPE_METHOD, INIT_TYPE_SEQ
from event_framework.event import META_EVENT_TYPE, META_EVENT_PRODUCER
from ext.ftp.ftp_client import Xfer as FTP_C


__author__ = 'chenxin'    
__date__ = '2017-4-13'  
__version__ = 1.0


class CsarProcessorScheduler(TaskScheduler):
    
    '''
    this task scheduler responds to handle the csar processing events,
    such as csar upload, csar onboarding, and etc.

    '''
    
    def __init__(self, conf_ctx, 
                       ctx_store, 
                       init_type=INIT_TYPE_METHOD,
                       init_job_seq=None, 
                       event_listener_list_syn=True, 
                       other_info={}):
        
        super(CsarProcessorScheduler, self).__init__(conf_ctx, 
                                                         ctx_store, 
                                                         init_type,
                                                         init_job_seq, 
                                                         event_listener_list_syn, 
                                                         other_info)
    
    def _init_method(self):

        '''
        init method called when the init type is INIT_TYPE_METHOD.
        derived task scheduler classes could override this method,
        initiation like static event listener registry, pre-defined
        context creation could be done in this method
        
        '''
        self._register_local_csar_upload_request_listener()
        self._register_csar_onboarding_request_listener()
        self._register_csar_info_acquiry_listener()
        self._create_catalogue_dirs()
        

    def _create_csar_id_namespace(self):

        '''
        create the namespace for csar id generation in the id generator
        not used currently

        '''
        id_gen = self.global_id_generator
        id_gen.add_dynamic_namespace(ID_NAMESPACE_CSAR, ID_NAMESPACE_CSAR)
    
    def _register_local_csar_upload_request_listener(self):

        '''
        register a event listener handling the local csar upload request,
        the csar upload request event is matched only by meta info:
            event_type: 'local_csar_upload_request'
            event_producer: 'local_rest_api'
        the event will be handled by trigger a processing of:
            job_unit_sequence: 'local_csar_upload_job_seq'

        '''
        e_type = self.get_event_type(EVENT_TYPE_LOCAL_CSAR_UPLOAD)
        e_producer = self.get_event_producer(EVENT_PRODUCER_LOCAL_REST)
        t_e_data = {}
        t_keys_list = []
        t_e_meta = {META_EVENT_TYPE: e_type, META_EVENT_PRODUCER: e_producer}
        t_meta_keys = [META_EVENT_TYPE, META_EVENT_PRODUCER]
        job_seq = self.get_job_unit_sequence(JOB_SEQ_LOCAL_CSAR_UPLOAD)
        self.task_event_listener_register(event_type=e_type, 
                                          target_e_data=t_e_data, 
                                          target_keys_list=t_keys_list,
                                          target_e_meta=t_e_meta, 
                                          target_e_meta_keys=t_meta_keys,
                                          job_unit_sequence=job_seq)
    
    def _register_csar_onboarding_request_listener(self):

        '''
        register a event listener handling the csar onboarding request,
        the csar onboarding request event is matched only by meta info:
            event_type: 'csar_onboarding_request'
            event_producer: 'local_rest_api'
        the event will be handled by trigger a processing of:
            job_unit_sequence: 'csar_onboarding_job_seq'

        '''
        e_type = self.get_event_type(EVENT_TYPE_CSAR_ONBOARDING)
        e_producer = self.get_event_producer(EVENT_PRODUCER_LOCAL_REST)
        t_e_data = {}
        t_keys_list = []
        t_e_meta = {META_EVENT_TYPE: e_type, META_EVENT_PRODUCER: e_producer}
        t_meta_keys = [META_EVENT_TYPE, META_EVENT_PRODUCER]
        job_seq = self.get_job_unit_sequence(JOB_SEQ_CSAR_ONBOARDING)
        self.task_event_listener_register(event_type=e_type, 
                                          target_e_data=t_e_data, 
                                          target_keys_list=t_keys_list,
                                          target_e_meta=t_e_meta, 
                                          target_e_meta_keys=t_meta_keys,
                                          job_unit_sequence=job_seq)
    
    def _register_csar_info_acquiry_listener(self):

        '''
        register a event listener handling the csar info acquiry,
        the csar info acquiry event is matched only by meta info:
            event_type: 'csar_info_acquire'
            event_producer: 'local_rest_api'
        the event will be handled by '_csar_info_acquire_handler'

        '''
        e_type = self.get_event_type(EVENT_TYPE_CSAR_INFO_ACQ)
        e_producer = self.get_event_producer(EVENT_PRODUCER_LOCAL_REST)
        t_e_data = {}
        t_keys_list = []
        t_e_meta = {META_EVENT_TYPE: e_type, META_EVENT_PRODUCER: e_producer}
        t_meta_keys = [META_EVENT_TYPE, META_EVENT_PRODUCER]
        self._event_listener_register(e_type, 
                                      t_e_data, 
                                      t_keys_list,
                                      t_e_meta, 
                                      t_meta_keys,
                                      self._csar_info_acquire_handler)
    
    def _csar_info_acquire_handler(self, **params):

        '''
        handler handling both the acquiries of all csar information
        and of a specified csar info by csar_id
        
        '''
        event = params['event']
        csar_id = event.get_event_data().get('csar_id', None)
        ctx_store = self.context_store
        if csar_id:
            h = ctx_store.get_context_item_process_handler(
                                            CONTEXT_NAMESPACE_CSAR, csar_id)
            event.set_return_data_asyn(h.get_context_item())
            h.process_finish()
            return
        ctx_handlers = ctx_store.get_context_namespace_process_handler(CONTEXT_NAMESPACE_CSAR)
        r_data = []
        for h in ctx_handlers:
            r_data.append(h.get_context_item())
            h.process_finish()
        event.set_return_data_asyn(r_data)

    
    def get_catalogue_serv_ip(self):
        
        '''
        get the catalogue service ip address
        
        '''
        remote_servs =  self.other_info.get('remoteServices', {})
        cata_serv = remote_servs.get('catalogue', {})
        return cata_serv.get('ip', None)

    def get_catalogue_serv_port(self):
        
        '''
        get the catalogue service ip address
        
        '''
        remote_servs =  self.other_info.get('remoteServices', {})
        cata_serv = remote_servs.get('catalogue', {})
        return cata_serv.get('port', None)

    def get_catalogue_serv_username(self):
        
        '''
        get the catalogue service username
        
        '''
        remote_servs =  self.other_info.get('remoteServices', {})
        cata_serv = remote_servs.get('catalogue', {})
        return cata_serv.get('username', None)

    def get_catalogue_serv_password(self):
        
        '''
        get the catalogue service password
        
        '''
        remote_servs =  self.other_info.get('remoteServices', {})
        cata_serv = remote_servs.get('catalogue', {})
        return cata_serv.get('password', None)

    def get_catalogue_serv_proto(self):
        
        '''
        get the catalogue service transport protocal
        
        '''
        remote_servs =  self.other_info.get('remoteServices', {})
        cata_serv = remote_servs.get('catalogue', {})
        return cata_serv.get('protocal', None)

    def get_catalogue_serv_dir(self):
        
        '''
        get the catalogue service dir architecture info
        
        '''
        remote_servs =  self.other_info.get('remoteServices', {})
        cata_serv = remote_servs.get('catalogue', {})
        return cata_serv.get('catalogueDir', {})

    def _create_catalogue_dirs(self):

        '''
        create the dirs in catalogue according to the dir achitecture info

        '''
        if self.get_catalogue_serv_proto() == PROTO_FTP:

            ftp_client = FTP_C()
            ftp_client.setFtpParams(self.get_catalogue_serv_ip(), 
                                    self.get_catalogue_serv_username(), 
                                    self.get_catalogue_serv_password())
            dirs = self.get_catalogue_serv_dir()
            for d in dirs.values():
                if os.path.exists('tmp'):
                    os.system('rm -r tmp')
                up_dir = os.path.join('tmp', d)
                os.makedirs(up_dir)
                ftp_client.upload('tmp')
                os.system('rm -r tmp')
