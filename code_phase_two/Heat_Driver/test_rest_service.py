#!/env/bin/python

#   test rest interface for the heat driver

import os
from flask import *


app = Flask(__name__)

SERV_PORT = 8093
SERV_IP = '0.0.0.0'
ROOT_PATH = '/5gslm/iaa'
HEAT_DRIVER = '/driver/heat/v1'

VNF_RES_DEPLOY = '/vnf/management/create/json'
VNF_RES_INFO = '/vnf/<vnf_res_id>/resource/json'

TEST_VNF_RES_ID_DICT = { ('WEB-LB-SUBNS-1', 'DB-NODE'): '1111', \
                         ('WEB-LB-SUBNS-1', 'LB-WEB-NODE'): '2222', \
                         ('WEB-LB-SUBNS-2', 'DB-NODE'): '3333', \
                         ('WEB-LB-SUBNS-2', 'LB-WEB-NODE'): '4444' }

R_DATA_DB_1 = {}
loc = R_DATA_DB_1
loc['vnfResStatus'] = 'deployment completes'
loc['relatedSliceResId'] = 'WEB-LB-SUBNS-1'
loc['vnfResId'] = '1111'
loc['decResId'] = 'core DC'
loc['relatedVimInfo'] = {}
loc['relatedVimInfo']['vimType'] = 'openstack'
loc['relatedVimInfo']['vimMgrEndPoint'] = '127.0.0.1'
loc['heatStackId'] = 'DB-NODE'
loc = loc.setdefault('outputInfo', {})
out_loc = loc.setdefault('CP_mgmtAgent_privateIp', {})
out_loc['value'] = '192.168.10.1/24'
out_loc = loc.setdefault('CP_mgmt_{{DB-NODE}}_privateIp', {})
out_loc['value'] = '192.168.10.2/24'
out_loc = loc.setdefault('CP_mgmtAgent_publicIp', {})
out_loc['value'] = '10.10.26.151/24'
out_loc = loc.setdefault('CP_{{DB-NODE}}_{{DB-PORTAL}}_publicIp', {})
out_loc['value'] = '10.10.26.152/24'

R_DATA_LB_WEB_1 = {}
loc = R_DATA_LB_WEB_1
loc['vnfResStatus'] = 'deployment completes'
loc['relatedSliceResId'] = 'WEB-LB-SUBNS-1'
loc['vnfResId'] = '2222'
loc['decResId'] = 'regional DC'
loc['relatedVimInfo'] = {}
loc['relatedVimInfo']['vimType'] = 'openstack'
loc['relatedVimInfo']['vimMgrEndPoint'] = '127.0.0.1'
loc['heatStackId'] = 'WEB-LB-NODE'
loc = loc.setdefault('outputInfo', {})
out_loc = loc.setdefault('CP_mgmtAgent_privateIp', {})
out_loc['value'] = '192.168.10.3/24'
out_loc = loc.setdefault('CP_mgmt_{{WEB-NODE}}_privateIp', {})
out_loc['value'] = '192.168.10.4/24'
out_loc = loc.setdefault('CP_mgmt_{{NGINX-NODE}}_privateIp', {})
out_loc['value'] = '192.168.10.5/24'
out_loc = loc.setdefault('CP_{{WEB-NODE}}_{{WEB-PORTAL}}_privateIp', {})
out_loc['value'] = '192.168.10.4/24'
out_loc = loc.setdefault('CP_{{NGINX-NODE}}_{{NGINX-PORTAL}}_privateIp', {})
out_loc['value'] = '192.168.10.5/24'
out_loc = loc.setdefault('CP_mgmtAgent_publicIp', {})
out_loc['value'] = '10.10.26.153/24'
out_loc = loc.setdefault('CP_{{WEB-NODE}}_{{WEB-PORTAL}}_publicIp', {})
out_loc['value'] = '10.10.26.154/24'
out_loc = loc.setdefault('CP_{{NGINX-NODE}}_{{NGINX-PORTAL}}_publicIp', {})
out_loc['value'] = '10.10.26.155/24'
out_loc = loc.setdefault('SP_WEB-SERVER-SCALE-OUT_url', {})
out_loc['value'] = 'http://127.0.0.1/scale/web/server/1'

R_DATA_DB_2 = {}
loc = R_DATA_DB_2
loc['vnfResStatus'] = 'deployment completes'
loc['relatedSliceResId'] = 'WEB-LB-SUBNS-2'
loc['vnfResId'] = '3333'
loc['decResId'] = 'core DC'
loc['relatedVimInfo'] = {}
loc['relatedVimInfo']['vimType'] = 'openstack'
loc['relatedVimInfo']['vimMgrEndPoint'] = '127.0.0.1'
loc['heatStackId'] = 'DB-NODE'
loc = loc.setdefault('outputInfo', {})
out_loc = loc.setdefault('CP_mgmtAgent_privateIp', {})
out_loc['value'] = '192.168.20.1/24'
out_loc = loc.setdefault('CP_mgmt_{{DB-NODE}}_privateIp', {})
out_loc['value'] = '192.168.20.2/24'
out_loc = loc.setdefault('CP_mgmtAgent_publicIp', {})
out_loc['value'] = '10.10.28.151/24'
out_loc = loc.setdefault('CP_{{DB-NODE}}_{{DB-PORTAL}}_publicIp', {})
out_loc['value'] = '10.10.28.152/24'

R_DATA_LB_WEB_2 = {}
loc = R_DATA_LB_WEB_2
loc['vnfResStatus'] = 'deployment completes'
loc['relatedSliceResId'] = 'WEB-LB-SUBNS-2'
loc['vnfResId'] = '4444'
loc['decResId'] = 'regional DC'
loc['relatedVimInfo'] = {}
loc['relatedVimInfo']['vimType'] = 'openstack'
loc['relatedVimInfo']['vimMgrEndPoint'] = '127.0.0.1'
loc['heatStackId'] = 'WEB-LB-NODE'
loc = loc.setdefault('outputInfo', {})
out_loc = loc.setdefault('CP_mgmtAgent_privateIp', {})
out_loc['value'] = '192.168.20.3/24'
out_loc = loc.setdefault('CP_mgmt_{{WEB-NODE}}_privateIp', {})
out_loc['value'] = '192.168.20.4/24'
out_loc = loc.setdefault('CP_mgmt_{{NGINX-NODE}}_privateIp', {})
out_loc['value'] = '192.168.20.5/24'
out_loc = loc.setdefault('CP_{{WEB-NODE}}_{{WEB-PORTAL}}_privateIp', {})
out_loc['value'] = '192.168.20.4/24'
out_loc = loc.setdefault('CP_{{NGINX-NODE}}_{{NGINX-PORTAL}}_privateIp', {})
out_loc['value'] = '192.168.20.5/24'
out_loc = loc.setdefault('CP_mgmtAgent_publicIp', {})
out_loc['value'] = '10.10.28.153/24'
out_loc = loc.setdefault('CP_{{WEB-NODE}}_{{WEB-PORTAL}}_publicIp', {})
out_loc['value'] = '10.10.28.154/24'
out_loc = loc.setdefault('CP_{{NGINX-NODE}}_{{NGINX-PORTAL}}_publicIp', {})
out_loc['value'] = '10.10.28.155/24'
out_loc = loc.setdefault('SP_WEB-SERVER-SCALE-OUT_url', {})
out_loc['value'] = 'http://127.0.0.1/scale/web/server/2'

R_DATA = { '1111': R_DATA_DB_1, \
           '2222': R_DATA_LB_WEB_1, \
           '3333': R_DATA_DB_2, \
           '4444': R_DATA_LB_WEB_2 }

@app.route(ROOT_PATH + HEAT_DRIVER + VNF_RES_DEPLOY, methods=['POST'])
def deploy_vnf_resource():
    if request.json:
        req = request.json
    if request.form:
        req = request.form
    
    print '#### HeatDriverTestRest: get vnf resource deploy with vnfd:'
    #   print yaml_ordered_dump(req['vnfdContent'], default_flow_style=False)
    r_data = {'status': 'request accepted'}
    #   print '!!!!!DEBUG: dict: ', TEST_VNF_RES_ID_DICT
    #   k = ('1806e4f0-96cb-3a37-922f-87abc1ee2684', 'DB-NODE')
    #   print '!!!!!DEBUG: res_id: ', str(req['sliceResId'])
    #   print '!!!!!DEBUG: in or not: ', k in TEST_VNF_RES_ID_DICT.keys()
    #   print '!!!!!DEBUG: eq or not:', str(req['sliceResId']) == str('1806e4f0-96cb-3a37-922f-87abc1ee2684')
    #   print '!!!!!DEBUG: cmp or not:', cmp(str(req['sliceResId']), str('1806e4f0-96cb-3a37-922f-87abc1ee2684'))
    vnf_res_id = TEST_VNF_RES_ID_DICT[(str(req['sliceResId']), str(req['vnfNodeId']))]
    r_data.update({'vnfResId': vnf_res_id})
    resp_d = jsonify(r_data)

    return resp_d, 201


@app.route(ROOT_PATH + HEAT_DRIVER + VNF_RES_INFO, methods=['GET'])
def acquire_vnf_resource_info(vnf_res_id):
    
    resp_d = jsonify(R_DATA[vnf_res_id])
    resp_d.headers['Access-Control-Allow-Origin'] = '*'

    return resp_d, 200



@app.errorhandler(500)
def error_occur(error):
    resp = jsonify({'error': 'unknown error'})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return make_response(resp, 500)

if __name__ == '__main__':
    
    app.run(host=SERV_IP, port=SERV_PORT)
