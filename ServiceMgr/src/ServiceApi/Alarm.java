package ServiceApi;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import java.util.Iterator;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Map;
import java.util.HashMap;

public class Alarm implements Runnable{
	//alarmInfoMap: <vnf_nid, alarmInfoList> . Each  list contains all the alarmId of this vnf
	private Map<String,List<AlarmFormat>> alarmInfoMap = Collections.synchronizedMap(new HashMap<String, 
			List<AlarmFormat>>());

	private String mongDbUrl = "";
	private String rawTemp = "";

	public Alarm(String mongDBUrl) {
		this.mongDbUrl = mongDBUrl;
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
	}
	
	/*
	 * refresh all monitortargets 
	 */
	private void copy() {
		for(String vnf : this.alarmInfoMap.keySet()) {
			for(AlarmFormat alarm : this.alarmInfoMap.get(vnf)) {
				alarm.copy();
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
