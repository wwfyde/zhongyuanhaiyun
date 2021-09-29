import json
import time
import httpx
data = {
    'businesstype': '1111111',
    'transfer': '1111111',
    'calltype': '1111111',
    'riskname': '1111111',
    'xbname': '1111111',
    'tyname': '1111111',
    'policyno': '1111111',
    'startdate': '1111111',
    'agent_id': '1111111',
    'staffname': '1111111',
    'relation_id': '1111111',
    'record_guid': '1111111',
    'ani': '1111111',
    'dnis': '1111111',
    'documentpath': '1111111',
    'starttime': '1111111',
    'insurance': '1111111',
    'summary': '1111111'
}

data_list = [data for i in range(1000)]

send_data = {'dataList': data_list}

headers = {'Content-Type': 'application/json'}
url = 'http://127.0.0.1:9001/receive'  # 10.1.10.91:8809
# request = .request.Request(url=url, headers=headers, data=bytes(json.dumps(send_data), 'utf8'))
# t1 = time.time()
# response = httpx.urlopen(request)
# t2 = time.time()
httpx.post(url, json=send_data)
# print(f"COST TIME: {t2-t1}")