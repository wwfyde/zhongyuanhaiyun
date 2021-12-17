import json
import httpx


def request_record_data(start_date: str, end_date: str) -> list:
    """
    请求呼叫中心接口数据
    :param start_date: 开始日期，yyyy-mm-dd
    :param end_date: 结束日期，yyyy-mm-dd
    :return: 数据列表
    """

    url: str = 'http://gateway.clmp-uat.csleasing.com.cn/hitf/v1/rest/invoke?namespace=HZERO&serverCode=CCUZ.CENTER.CALL&interfaceCode=clmp-customize.udeskcallcentercalllog.queryAllType'
    token_url: str = 'http://gateway.clmp-uat.csleasing.com.cn/oauth/oauth/token?grant_type=client_credentials&client_id=clms-client&client_secret=clms-secret&scope=default'
    page_size: str = '100'
    # 测试时启用

    # url = 'http://gateway.clmp-uat.csleasing.com.cn/hitf/v1/rest/invoke?namespace=HZERO
    # &serverCode=CCUZ.CENTER.CALL&interfaceCode=clmp-customize.udeskcallcentercalllog.queryAllType'
    # token_url = 'http://gateway.clmp-dev.csleasing.com.cn/oauth/oauth/token?
    # grant_type=client_credentials&client_secret=clcms-secret&client_id=clcms-client'
    try:
        access_token = 'Bearer ' + json.loads(
            httpx.post(token_url, headers={'Content-type': 'application/x-www-form-urlencoded'},
                       timeout=40).text)['access_token']

        # TODO 需要进行分页处理下载
        resp = httpx.post(url, json={
            "pathVariableMap": {
                "organizationId": 0
            },
            "requestParamMap": {
                "startingTime": start_date,
                "stopTime": end_date,
                "pageSize": page_size,
            },
        }, headers={'Authorization': access_token}, timeout=40)
        # 似乎不需要replace \\
        r: dict = json.loads(resp.text)
        receive_data = []  #
        if str(r["status"]) == "200":
            receive_data: list = json.loads(r["payload"])["content"]
            total_pages = int(json.loads(r["payload"])["totalPages"])

            if total_pages > 1:
                for start_page in range(2, total_pages+1):
                    resp2 = httpx.post(url, json={
                        "pathVariableMap": {
                            "organizationId": 0
                        },
                        "requestParamMap": {
                            "startingTime": start_date,
                            "stopTime": end_date,
                            "startPage": start_page,
                            "pageSize": page_size,
                        },
                    }, headers={'Authorization': access_token}, timeout=40)
                    # 似乎不需要replace \\
                    r2: dict = json.loads(resp2.text)
                    receive_data.extend(json.loads(r2["payload"])["content"])

            print(f"获取录音记录列表成功, 录音列表: {receive_data}, 共 [{len(receive_data)}]条记录, 共{ total_pages} 页")
            # for data in receive_data_raw:
            #     item = dict(
            #
            #     )

        else:
            print(f"请求录音记录返回了错误的提示信息, 错误码: {r['status']}")
            receive_data = []

        # 格式化数据
        # for data in receive_data_raw:
        #     receive_data.append(dict(
        #         record_id=data['call_id'],  # 录音id
        #         start_time=data['startTime'],  # 通话开始时间
        #         end_time=data['endTime'],  # 通话结束时间
        #         call_no=data['CallNo'],  #
        #     ))

        """
        示例
        [{
            "appointid": 33036, 
            "callID": "1625470045.244822",
            "conversationId": null,
            "timestamp": "2021-07-05 15:27:39",
            "nickName": null,
            "customerPhone": "15275589622",
            "mobileArea": null,
            "displayNumber": null,
            "workflow": "dialout",
            "fromAgentId": null,
            "callResult": "dealing",
            "isLeavellessage": null,
            "totalTime": 114,
            "recordUrl": "http://10.25.7.100:8990/monitor/1.2.136.101/20210705/20210705-152726 N000000011288 15275589622 
            915275589622 1625470045.244822.mp3",
            "survey": null,
            "outlinePhoneNumber": null,
            "agentId": 8002,
            "customerRingAt": null,
            "customerAnswerAt": null,
            "agentAnswerAt": null,
            "pullRecordUrls": "http://minio-7c27d1.camp-uat-upgrade:9000/hzero-hzero-public/0
            /b7b735d91675483a9766c267aa6db191@hollyCrm-1625470045.244822.mp3",
        }]

        """
        return receive_data
    except Exception as exc:
        print(f"请求第三方接口失败, 请检查接口包含token获取接口是否正常, \n 错误提示: {exc}")
        return []

    # app_id = "qualityclient"
    # app_secret = "BzVSUmeY2FRzx8Jf791d3wSGdR2FkyGfi0"
    # nonce = ''.join(random.sample(string.ascii_letters + string.digits, 32))
    # t = int(time.time())
    # sign_str = f"Appid={app_id}&AppSecret={app_secret}&Nonce={nonce}&Time={t}"
    # sign = hashlib.md5(sign_str.encode(encoding='UTF-8')).hexdigest().upper()
    # data = {
    #     "startTime": start_date,
    #     "endTime": end_date,
    #     "Appid": app_id,
    #     "Nonce": nonce,
    #     "Time": t,
    #     "Sign": sign
    # }
    # resp = requests.post(url, json=data)  # 请求requests数据
    # data_receive = resp.json()
    # if data_receive["code"] != "0":
    #     log.error(f"录音数据请求失败 {data_receive}")
    #     return None
    # log.info(f"录音数据请求成功，数据量：{len(data_receive['Data'])}")
    # return data_receive["Data"]


if __name__ == '__main__':
    request_record_data('2021-11-25 00:00:00', '2021-11-25 23:59:59')

