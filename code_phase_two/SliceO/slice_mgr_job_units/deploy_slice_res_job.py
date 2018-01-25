#   The class of the slice resource deployment job unit


import os
import time
from collections import OrderedDict
from copy import deepcopy

from common.util import get_class_func_name, CONTEXT_NAMESPACE_SLICE, \
                                          COMPONENT_NAME_E2E_RES_MGR, SERVICE_SLICE_RES_DEPLOY, SERVICE_SLICE_RES_ACQUIRE, \
                                          SLICE_STATUS_RES_COMPLETE, SLICE_STATUS_RES_FAIL, \
                                          SLICE_RES_STATUS_DEPLOYING, SLICE_RES_STATUS_COMPLETE, SLICE_RES_STATUS_FAIL
from common.yaml_util import yaml_ordered_dump as yaml_dump
from event_framework.job_unit import JobUnit
from event_framework.event import META_EVENT_TYPE, META_EVENT_PRODUCER
import urllib2
import json
__author__ = 'chenxin'    
__date__ = '2017-4-18'  
__version__ = 1.0



class SliceResDeployJob(JobUnit):
    
    '''
    this job is used to request the e2e resource manager to deploy the slice resource.
    this job get inputs:
        slice_id:
    the works done by this job are:
        send a slice resource deployment request to remote service
        periodically check the remote service whether the deployment completes

    '''
    
    
    def __init__(self, task_unit, job_n, **params):
        
        '''
        params:
            task_unit: the task unit instance this job unit belongs to
            job_n: the name of this job given in the job unit sequence
            params: other parameters may used for extension
        '''
        super(SliceResDeployJob, self).__init__(task_unit, job_n, **params)

    def execute_job(self, **params):

        '''
        called by the task unit to start the execution of this job.
        derived job unit class should override this method to deploy own processing logic

        '''
        
        try:
            print "#######", params
            self.slice_id = params['slice_id']
            resp = self._send_res_deploy_req()
            if 'sliceResId' not in resp.keys():
                raise Exception('#### SliceResDeployJob: slice resource deployment request failed')
            self.slice_res_id = resp['sliceResId']
            print '#### SliceResDeployJob: get a slice resource Id: ' + self.slice_res_id
            self._wait_slice_res_deploy()
            self._update_slice_ctx()
            self._deploy_monitor_options()
            self._deploy_alarms()
            self._execution_finish()
        except Exception, e:
            print Exception, ':', e, \
                      ' in %s:%s' % get_class_func_name(self)
            self._execution_exception(Exception, e)
        

    
    
    def _send_res_deploy_req(self):

        '''
        send slice resource deployment request to the remote service, including:
            read the slice resource context
            generate request data
            send request to the remote service
        return the response

        '''
        ctx_store = self.task_unit.task_scheduler.context_store
        ctx_h = ctx_store.get_context_item_process_handler(CONTEXT_NAMESPACE_SLICE, self.slice_id)
        res_ctx = ctx_h.get_context_item()['resourceInfo']
        req_data = OrderedDict()
        req_data['sliceId'] = self.slice_id

        req_data['nsdContent'] = res_ctx['nsResInfo']['nsdContent']

        req_data['vnfInfo'] = OrderedDict()
        for vnf_nid, vnf_res_v in res_ctx['nsResInfo']['vnfResInfo'].items():
            res = req_data['vnfInfo'].setdefault(vnf_nid, OrderedDict())
            res['dcResId'] = vnf_res_v['datacenterId']
            res['vnfdContent'] = vnf_res_v['vnfdContent']
        
        ctx_h.process_finish()
        print "#######debug: #####", req_data
        return self.task_unit.task_scheduler.\
                         req_remote_serv(COMPONENT_NAME_E2E_RES_MGR, SERVICE_SLICE_RES_DEPLOY, req_data)

    def _wait_slice_res_deploy(self):

        '''
        periordically check the remote service until the slice resource deployment completes

        '''
        url_para = {'slice_res_id': self.slice_res_id}
        res_status = SLICE_RES_STATUS_DEPLOYING

        while res_status == SLICE_RES_STATUS_DEPLOYING:
            time.sleep(5)
            self.deploy_resp = self.task_unit.task_scheduler.\
                         req_remote_serv(COMPONENT_NAME_E2E_RES_MGR, SERVICE_SLICE_RES_ACQUIRE, {}, **url_para)
            res_status = self.deploy_resp.get('sliceResGlobalStatus', SLICE_RES_STATUS_FAIL)
        
        if res_status == SLICE_RES_STATUS_FAIL:
            ctx_store = self.task_unit.task_scheduler.context_store
            ctx_h = ctx_store.get_context_item_process_handler(CONTEXT_NAMESPACE_SLICE, self.slice_id)
            ctx_h.get_context_item()['status'] = SLICE_STATUS_RES_FAIL
            ctx_h.process_finish()
            raise Exception('#### SliceResDeployJob: slice resource deployment request failed')
        
        ctx_store = self.task_unit.task_scheduler.context_store
        ctx_h = ctx_store.get_context_item_process_handler(CONTEXT_NAMESPACE_SLICE, self.slice_id)
        ctx = ctx_h.get_context_item()
        ctx['status'], ctx['resourceInfo']['sliceResId'] = SLICE_STATUS_RES_COMPLETE, self.slice_res_id
        ctx_h.process_finish()
        #   print '#### SliceResDeployJob: slice vnf resource deployment completes with slice resource id: ' + self.slice_res_id
        #   print yaml_dump(self.deploy_resp, default_flow_style=False)

    def _deploy_monitor_options(self):
        ctx_store = self.task_unit.task_scheduler.context_store
        ctx_h = ctx_store.get_context_item_process_handler(CONTEXT_NAMESPACE_SLICE, self.slice_id)
        vnf_res_ctx = ctx_h.get_context_item()['resourceInfo']['nsResInfo']['vnfResInfo']
        vnf_conf_ctx = ctx_h.get_context_item()['configInfo']
        monitor_options = ctx_h.get_context_item()['metadata']['monitorOptions']
        ns_monitor = {
            'flag': 'monitor'
        }
        ns_scaling_policy = {}
        print "deploy monitor options step 1"
        for vnf_nid, vnf_value in vnf_res_ctx.items():
            vnf_monitor = ns_monitor.setdefault(vnf_nid, {})
            vnf_monitor['Info'] = {
                'vnfNodeId': vnf_nid
            }
            vnf_scaling = vnf_value['vnfScalingPolicyInfo']
            vnf_monitor['VnfcNodes'] = []
            vnf_scaling_police = ns_scaling_policy.setdefault(vnf_nid, {})
            print "deploy monitor options step 2"
            print vnf_nid
            for vnfc_nid, vnfc_value in vnf_value['vnfcResInfo'].items():
                vnfc_scaling_policy = vnf_scaling_police.setdefault(vnfc_nid, {})
                for policy_key, policy_value in vnf_scaling.items():
                    if policy_value['targetVnfcNodeIdList'][0] == vnfc_nid:
                        if policy_key.endswith('OUT'):
                            vnfc_scaling_policy['out'] = policy_value['rtTriggerUrl']
                        elif policy_key.endswith('IN'):
                            vnfc_scaling_policy['in'] = policy_value['rtTriggerUrl']
                ip_list = []
                for end_point in vnfc_value['vnfcEndPointResInfo'].values():
                    ip_list = end_point['rtPrivateIpList']
                    break
                print "ip list"
                print ip_list
                vnfc_info = {
                    'vnfcNodeId': vnfc_nid,
                    'ip': ip_list[0],
                    'scaleIn': vnfc_scaling_policy['in'],
                    'scaleOut': vnfc_scaling_policy['out']
                }
                vnf_monitor['VnfcNodes'].append(vnfc_info)
                print "vnf_monitor"
                print vnf_monitor
            mgmt_host = vnf_conf_ctx[vnf_nid]['mgmtAgentHostInfo']
            mgmt_id = mgmt_host['vduId']
            mgmt_public_ip = mgmt_host['mgmtEndPointInfo']['rtPublicIp']
            vnf_monitor['MgmtNode'] = {
                'vnfcNodeId' : mgmt_id,
                'ip': mgmt_public_ip
            }
            vnf_monitor['MonitorOptions'] = []
            for monitor_option in monitor_options:
                for key, value in monitor_option.items():
                    params = value['parameters']
                    param = params[0]
                    for v in param.values():
                        print "paramOne"
                        target_vnf_node = v['target'][0]
                        if vnf_nid == target_vnf_node:
                            vnf_monitor['MonitorOptions'].append(monitor_option)
        print "====================watch me : ns monitor =================\n"
        print ns_monitor
        body = json.dumps(ns_monitor)
        self._send_serviceMgr(body)

    def _deploy_alarms(self):
        ctx_store = self.task_unit.task_scheduler.context_store
        ctx_h = ctx_store.get_context_item_process_handler(CONTEXT_NAMESPACE_SLICE, self.slice_id)
        alarm_info = ctx_h.get_context_item()['metadata']['alarmInfo']
        alarm_serviceMgr = {
            'alarmInfo': alarm_info,
            'flag': 'alarm',
            'nsTypeId': ctx_h.get_context_item()['metadata']['Info']['nsTypeId']
        }
        print alarm_serviceMgr
        body = json.dumps(alarm_serviceMgr)
        self._send_serviceMgr(body)

    def _send_serviceMgr(self, body):
        url = 'http://192.168.0.20:8080/ServiceMgr/hello'
        http_req = urllib2.Request(url=url, data=body)
        http_req.add_header('Content-type', 'application/json')
        urllib2.urlopen(http_req)

    def _update_slice_ctx(self):

        '''
        update the slice context using the slice resource deployment response,
        including the slice resource context and the slice config context

        '''
        ctx_store = self.task_unit.task_scheduler.context_store
        ctx_h = ctx_store.get_context_item_process_handler(CONTEXT_NAMESPACE_SLICE, self.slice_id)
        vnf_res_resp = self.deploy_resp['vnfResInfo']
        
        ############ update the slice resource context #############
        vnf_res_ctx = ctx_h.get_context_item()['resourceInfo']['nsResInfo']['vnfResInfo']
        for vnf_nid, ctx_v in vnf_res_ctx.items():
            resp_v = vnf_res_resp[vnf_nid]
            resp_vdu, resp_cp, resp_sp = resp_v['vduInfo'], resp_v['cpInfo'], resp_v['spInfo']
            ctx_v['rtVimType'] = resp_v['relatedVimInfo']['vimType']
            ctx_v['rtVimMgrEndPoint'] = resp_v['relatedVimInfo']['vimMgrEndPoint']
            
            for vnfc_res in ctx_v['vnfcResInfo'].values():
                for vnfc_ep_res in vnfc_res['vnfcEndPointResInfo'].values():
                    vnfc_res['rtVmNum'] = len(resp_cp.get(vnfc_ep_res['cpId'], {}).get('privateIpInfo', {}).get('ipList', []))
                    vnfc_ep_res['rtPrivateIpList'] = resp_cp.get(vnfc_ep_res['cpId'], {}).get('privateIpInfo', {}).get('ipList', [])
                    vnfc_ep_res['rtPrivateIpList'] = [str(n['privateIp']) for n in vnfc_ep_res['rtPrivateIpList']]
                    
                    #   print '#### SliceResDeployJob: the value of vnfc endpoint private ip list: '
                    #   print vnfc_ep_res['rtPrivateIpList']
                    
                    vnfc_ep_res['rtPublicIpList'] = resp_cp.get(vnfc_ep_res['cpId'], {}).get('publicIpInfo', {}).get('ipList', [])
                    vnfc_ep_res['rtPublicIpList'] = [str(n['publicIp']) for n in vnfc_ep_res['rtPublicIpList']]

                    #   print '#### SliceResDeployJob: the value of vnfc endpoint public ip list: '
                    #   print vnfc_ep_res['rtPublicIpList']
            
            for ep_res in ctx_v['vnfEndPointResInfo'].values():
                ep_res['rtPublicIpList'] = resp_cp.get(ep_res['relatedCpId'], {}).get('publicIpInfo', {}).get('ipList', [])
                ep_res['rtPublicIpList'] = [str(n) for n in ep_res['rtPublicIpList']]
                
                #   print '#### SliceResDeployJob: the value of vnf endpoint public ip list: '
                #   print ep_res['rtPublicIpList']
            
            for sp_res in ctx_v.get('vnfScalingPolicyInfo', {}).values():
                sp_res['rtTriggerUrl'] = resp_sp.get(sp_res['vnfdSpId'], {}).get('triggerUrl', None)
            print '#### SliceResDeployJob: slice vnf resource context updated with slice id: ' + self.slice_id
            print yaml_dump(vnf_res_ctx, default_flow_style=False)

        
        ############ update the slice config context ##########
        vnf_conf_ctx = ctx_h.get_context_item()['configInfo']
        for vnf_nid, ctx_v in vnf_conf_ctx.items():
            resp_v = vnf_res_resp[vnf_nid]
            resp_vdu, resp_cp = resp_v['vduInfo'], resp_v['cpInfo']

            #   update the context of management agent host in each vnf node
            mg_host_ctx = ctx_v['mgmtAgentHostInfo']
            mg_host_ep_ctx = mg_host_ctx['mgmtEndPointInfo']
            log_info = resp_vdu[mg_host_ctx['vduId']]['loginInfo']
            u_name, p_word = log_info['username'], log_info['password']
            pub_ip_l = resp_cp[mg_host_ep_ctx['cpId']]['publicIpInfo']['ipList']
            pri_ip_l = resp_cp[mg_host_ep_ctx['cpId']]['privateIpInfo']['ipList']
            mg_host_ep_ctx['rtPrivateIp'], mg_host_ep_ctx['rtPublicIp'], mg_host_ep_ctx['rtUsername'], mg_host_ep_ctx['rtPassword'] = \
                        pri_ip_l[0], pub_ip_l[0], u_name, p_word

            #   update the config context of each vnfc node
            for vnfc_nid, vnfc_conf in ctx_v['vnfcMgmtInfo'].items():
                mg_ep_ctx, prop_ctx = vnfc_conf['mgmtEndPointInfo'], vnfc_conf['configPropertyInfo']
                
                #   update the management endpoint context of each vnfc node
                log_info = resp_vdu[vnfc_conf['vduId']]['loginInfo']
                u_name, p_word = log_info['username'], log_info['password']
                pri_ip_l = resp_cp[mg_ep_ctx['cpId']]['privateIpInfo']['ipList']
                u_name_l, p_word_l = [u_name] * len(pri_ip_l), [p_word] * len(pri_ip_l)
                mg_ep_ctx['rtPrivateIpList'], mg_ep_ctx['rtUsernameList'], \
                          mg_ep_ctx['rtPasswordList'] = pri_ip_l, u_name_l, p_word_l

                #   update the configurable properties context of each vnfc node
                #   for the independent properties
                for prop, prop_ctx_v in prop_ctx.get('independentParas', {}).items():
                    prop_ctx_v['rtValue'] = dict(zip(pri_ip_l, [prop_ctx_v['value']] * len(pri_ip_l)))
                    if prop_ctx_v['isBuildInFunc']:
                        prop_ctx_v['rtValue'] = \
                              self._get_value_from_buildin_func(prop_ctx_v['value'], vnf_res_ctx, vnf_nid, vnfc_nid, mg_ep_ctx)
        
        #   update the context for dependent properties
        for vnf_nid, ctx_v in vnf_conf_ctx.items():
            for vnfc_nid, vnfc_conf in ctx_v['vnfcMgmtInfo'].items():
                mg_ep_ctx, prop_ctx, if_ctx = vnfc_conf['mgmtEndPointInfo'], vnfc_conf['configPropertyInfo'], vnfc_conf['interfaceInfo']

                #   update the context of dpendent properties
                for prop, prop_ctx_v in prop_ctx.get('dependentParas', {}).items():
                    prop_ctx_v['rtValue'] = self._get_dependent_value(prop_ctx_v['dependency'], vnf_conf_ctx, mg_ep_ctx)
        
        print '#### SliceResDeployJob: slice vnf config context updated with slice id: ' + self.slice_id
        print yaml_dump(vnf_conf_ctx, default_flow_style=False)
        
        ctx_h.process_finish()
    
    
    
    def _get_value_from_buildin_func(self, bi_func, vnf_res_ctx, vnf_nid, vnfc_nid, vnfc_mg_ep_ctx):

        '''
        get the runtime value from a buildin function for a configurable property
        params:
            bi_func: the string of the buildin function
            vnf_res_ctx: resource context of all the vnf nodes in the current slice
            vnf_nid: the vnf node id to which the property belongs to
            vnfc_nid: the vnfc node id to which the property belongs to
            vnfc_mg_ep_ctx: the context of the management endpoint of the vnfc node to which the property belongs to
        return:
            a dict with the key as the ip of the management endpoint of the instance, and the runtime value of the 
            property for the corresponding instance

        '''
        func_t, ep_id = bi_func.strip('{{').strip('}}').strip().split(':')
        func_t, ep_id = func_t.strip(), ep_id.strip()
        ep_res_info = vnf_res_ctx[vnf_nid]['vnfcResInfo'][vnfc_nid]['vnfcEndPointResInfo'][ep_id]
        rt_v_l = ep_res_info.get('rtPrivateIpList', [])
        if func_t == 'get_publicIp':
            rt_v_l = ep_res_info.get('rtPublicIpList', [])
        return dict(zip(vnfc_mg_ep_ctx['rtPrivateIpList'], rt_v_l))

    def _get_dependent_value(self, dep_ctx, vnf_conf_ctx, vnfc_mg_ep_ctx):

        '''
        get the runtime value of a dependent property
        params:
            dep_ctx: the context of the dependency 
            vnf_conf_ctx: config context of all the vnf nodes in the current slice
            vnfc_mg_ep_ctx: the context of the management endpoint of the vnfc node to which the property belongs to
        return:
            a dict with the key as the ip of the management endpoint of the instance, and the runtime value of the 
            property for the corresponding instance

        '''
        dep_vnf_nid, dep_vnfc_nid, dep_prop, m_ins_opt = \
                   dep_ctx['vnfNodeId'], dep_ctx['vnfcNodeId'], dep_ctx['propertyId'], dep_ctx['multiInstanceOption']
        dep_vnfc_prop_ctx = vnf_conf_ctx[dep_vnf_nid]['vnfcMgmtInfo'][dep_vnfc_nid]['configPropertyInfo']
        if dep_prop in dep_vnfc_prop_ctx.get('independentParas', {}):
            dep_rt_v_l = dep_vnfc_prop_ctx['independentParas'][dep_prop]['rtValue'].values()
            if not m_ins_opt:
                dep_rt_v_l = dep_rt_v_l[0]
            return dict(zip(vnfc_mg_ep_ctx['rtPrivateIpList'], [dep_rt_v_l] * len(vnfc_mg_ep_ctx['rtPrivateIpList'])))
        if dep_prop in dep_vnfc_prop_ctx.get('dependentParas', {}):
            raise Exception('#### SliceResDeployJob: only an independent parameter could be depended on')
