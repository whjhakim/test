package ServiceApi;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import java.util.Iterator;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.concurrent.FutureTask;
import java.util.HashMap;
import Mongo.MongoApi;

public class Alarm implements Runnable{
	//alarmInfoMap: <vnf_nid, alarmInfoList> . Each  list contains all the alarmId of this vnf
	private Map<String,List<AlarmFormat>> alarmInfoMap = Collections.synchronizedMap(new HashMap<String, 
			List<AlarmFormat>>());
	private Map<String,JSONObject> targetMaterials = new HashMap<String,JSONObject>();

	private String mongDbUrl = "";
	private String rawTemp = "";
	private MongoApi mongoApi;

	public Alarm(String mongDBUrl, MongoApi mongo) {
		this.mongDbUrl = mongDBUrl;
		this.mongoApi = mongo;
	}

	public void start() {
		System.out.println("alamr starts");
	}

	public void run() {
		System.out.println("alarm begins running");
		try {
			while(true) {
				// this request must contains all the monitor target
				this.sendToMongDB();
				this.copy();
				Thread.sleep(20000);
			}
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	/*
	 * request all monitorTarges of all vnfs
	 */
	private void sendToMongDB() {
		for(String vnf_nid : this.alarmInfoMap.keySet()) {
			JSONObject vnfMonitorTarget = this.mongoApi.getVnfMonitorTarget(vnf_nid);
			this.targetMaterials.put(vnf_nid, vnfMonitorTarget);
		}
	}
	
	/*
	 * refresh all monitortargets 
	 */
	private void copy() {
		for(String vnf : this.alarmInfoMap.keySet()) {
			//string is the alarm id
			Map<String,FutureTask<Integer>> futureMap = new HashMap<String, FutureTask<Integer>>();
			JSONObject monitorTargets = this.targetMaterials.get(vnf);
			for(AlarmFormat alarm : this.alarmInfoMap.get(vnf)) {
				Callable<Integer> callable = new Callable<Integer>() {
					public Integer call() throws Exception{
						try {
							alarm.copy(monitorTargets);
						}catch(Exception e) {
							return -1;
						}
						return 0;
					}
				};
				FutureTask<Integer> future = new FutureTask<Integer>(callable);
				String alarmId = alarm.getAlarmId();
				futureMap.put(alarmId, future);
				new Thread(future).start();
			}

			while(true) {
				boolean allDone = true;
				for(String alarmId : futureMap.keySet()) {
					if(!futureMap.get(alarmId).isDone()) {
						allDone = false;
						break;
					}
				}
				if(allDone) {
					break;
				}
				try {
					Thread.sleep(1000);
				}catch(Exception e) {
					e.printStackTrace();
				}
			}
		}
	}
	
	public JSONObject getAlarmsStatus(String vnf) {
		List<AlarmFormat> alarmList = this.alarmInfoMap.get(vnf);
		JSONObject returnObj = new JSONObject();
		for(AlarmFormat format : alarmList) {
			String alarmId = format.getAlarmId();
			String status = format.getAlarmStatus();
			returnObj.put(alarmId, status);
		}
		return  returnObj;
	}
	
	public void addAlarmInfo(JSONObject alarm) {
		String vnf = alarm.getString("VnfNodeId");
		JSONObject alarmInfo = JSONObject.fromObject(alarm.get("alarmInfo"));
		Iterator<Object> alarmKey = alarmInfo.keys();
		while(alarmKey.hasNext()) {
			String alarmId = String.valueOf(alarmKey.next());
			JSONObject alarmEntry = alarmInfo.getJSONObject(alarmId);
			AlarmFormat alarmFormat = new AlarmFormat(alarmId,alarmEntry);
			this.alarmInfoMap.get(vnf).add(alarmFormat);
		}
	}
}
