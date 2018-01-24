#!/env/bin/python

#   rest interface for the openstack rest proxy

import os
from flask import *
from ext.openstackclient.os_rest_client import OsRestClient


DC_INFO = [ \
           {'dc_id': 'datacenter_local', 'vim_type': 'openstack', 'vim_addr': '192.168.136.11', \
            'username': 'demo', 'password': 'demo', 'tenantname': 'teststack_large'}, \
          ]


app = Flask(__name__)

SERV_PORT = 8092
SERV_IP = '0.0.0.0'
ROOT_PATH = '/5gslm/iaa'
SLICE_MGR= '/sliceOM/v1'
DC_RESOURCE = '/infrastructure/resource/datacenter/json'


@app.route(ROOT_PATH + SLICE_MGR + DC_RESOURCE, methods=['GET'])
def get_global_resource():
    resp = []
    for dc in DC_INFO:
        os_client = OsRestClient(dc['vim_addr'], dc['username'], 
                                 dc['password'], dc['tenantname'])
        dc_res = {}
        dc_res['dc_resource_id'] = dc['dc_id']
        dc_res['vim_type'] = dc['vim_type']
        dc_res['vim_mgmt_address'] = os_client.get_os_login_addr()
        stat_info = os_client.get_hypervisors_stat()
        dc_res['running_vm_num'] = stat_info['running_vms']
        dc_res['disk_total_gb'] = stat_info['local_gb']
        dc_res['disk_used_gb'] = stat_info['local_gb_used']
        dc_res['memory_total_mb'] = stat_info['memory_mb']
        dc_res['memory_used_mb'] = stat_info['memory_mb_used']
        dc_res['cpu_total'] = stat_info['vcpus']
        dc_res['cpu_used'] = stat_info['vcpus_used']

        resp.append[dc_res]


    resp_d = jsonify(resp)
    resp_d.headers['Access-Control-Allow-Origin'] = '*'

    return resp_d, 201




@app.errorhandler(500)
def error_occur(error):
    resp = jsonify({'error': 'unknown error'})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return make_response(resp, 500)

if __name__ == '__main__':
    
    app.run(host=SERV_IP, port=SERV_PORT)