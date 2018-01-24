package Mongo;
import com.mongodb.client.FindIterable;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoCursor;
import com.mongodb.client.MongoDatabase;

import org.bson.Document;

import com.mongodb.MongoClient;
import com.mongodb.MongoClientOptions;

import net.sf.json.JSONObject;

public class MongoApi {
	private MongoClient mongoClient;
	private MongoDatabase mongoDatabase;
	private MongoClientOptions.Builder options = new MongoClientOptions.Builder();
	private MongoClientOptions mongoOptions;
	//private ServerAddress serverAddress;
	//private List<ServerAddress> addrs = new ArrayList<ServerAddress>();
	//private MongoCredential credential;
	//private List<MongoCredential> credentials = new ArrayList<MongoCredential>();
	public MongoApi(String ip) {
		//this.serverAddress = new ServerAddress(ip,27017);
		//this.addrs.add(this.serverAddress);

		//this.credential = MongoCredential.createScramSha1Credential("serviceMgr", "vnf", "123456".toCharArray());
		//this.credentials.add(credential);

		this.options.socketTimeout(0);
		this.options.connectTimeout(30000);
		this.options.maxWaitTime(5000);
		this.mongoOptions = options.build();
		this.mongoClient = new MongoClient(ip,this.mongoOptions);
		this.mongoDatabase = this.mongoClient.getDatabase("vnf");
	}

	public MongoApi() {
		this("192.168.0.20");
	}
	
	public JSONObject getVnfMonitorTarget(String vnf) {
		JSONObject vnfMonitor = new JSONObject();
		MongoCollection<Document> collection = this.mongoDatabase.getCollection(vnf);
		FindIterable<Document> iterator = collection.find();
		MongoCursor<Document> mongoCursor = iterator.iterator();
		while(mongoCursor.hasNext()) {
			Document doc = mongoCursor.next();
			String monitorTarget = String.valueOf(doc.get("monitortarget"));
			String value = String.valueOf(doc.get("value"));
			vnfMonitor.put(monitorTarget, value);
		}
		return vnfMonitor;
	}

/*	public static void main(String[] args) {
		MongoApi mongo = new MongoApi();
		JSONObject obj = mongo.getVnfMonitorTarget("vnfc1");
		System.out.println(obj);
	}*/
}
