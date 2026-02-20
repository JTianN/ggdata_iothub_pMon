็How to start server : Go with CMD --> python -m uvicorn main:app --reload

example .env
LOCATIONS_JSON=[
 {"location_id":"k-ifarm","latitude":13.7563,"longitude":100.5018},
 {"location_id":"k-ifarm2","latitude":13.70,"longitude":100.60}
]

IOT_CONN_K_IFARM=xxxxx
IOT_CONN_K_IFARM2=xxxxx
////////////////////////////////////////////////////////////////////////////////////////////////////


////////////////////////////////////////////////////////////////////////////////////////////////////
ตัวอย่าง Azure Environment Variables
GOOGLE_API_KEY=xxxxxxxx
SEND_INTERVAL_SEC=60

LOCATIONS_JSON=[{"location_id":"k-ifarm","latitude":13.7563,"longitude":100.5018},
{"location_id":"k-ifarm2","latitude":13.70,"longitude":100.60}]

IOT_CONN_K_IFARM=HostName=....
IOT_CONN_K_IFARM2=HostName=....

format ต้องตั้งตามนี้
| location_id | ENV name         |
| ----------- | ---------------- |
| k-ifarm     | IOT_CONN_K_IFARM |
| farm-01     | IOT_CONN_FARM_01 |




////////////////////////////////////////////////////////////////////////////////////////////////////
