package ServiceApi; 
public class AlertFormat {
	private String expression;
	private String url = "";
	public AlertFormat(String expression,String url) {
		this.expression = expression;
		this.url = url;
	}
	
	public String getExpression() {
		return this.expression;
	}
	
	public String getUrl() {
		return this.url;
	}
	
	public String scale(String vnfTypeId) {
		//send message to O&M must contain the url,this url is not scaling url ,but the o&m url for scaling
		String reply = "null";
		return reply;
	}
	
	public boolean compare(String value) {
		String script = value + this.expression;
		boolean returnValue = false;
		try {
			returnValue = (boolean)MonitorFormat.jse.eval(script);
		}catch(Exception e) {
			e.printStackTrace();
		}
		return returnValue;
	}
}
