import json


import httpx


def request_record_data(start_date: str, end_date: str) -> list:
    # 测试时启用

    url = 'http://gateway.clmp-uat.csleasing.com.cn/hitf/v1/rest/invoke?namespace=HZERO&serverCode=CCUZ.CENTER.CALL&interfaceCode=clmp-customize.udeskcallcentercalllog.queryAllType'
    token_url = 'http://gateway.clmp-uat.csleasing.com.cn/oauth/oauth/token?grant_type=client_credentials&client_id=clms-client&client_secret=clms-secret&scope=default'
    try:
        access_token = 'Bearer ' + json.loads(
            httpx.post(token_url, headers={'Content-type': 'application/x-www-form-urlencoded'}).text)['access_token']

        resp = httpx.post(url, json={
            "pathVariableMap": {
                "organizationId": 0
            },
            "requestParamMap": {
                "startingTime": start_date,
                "stopTime": end_date,
            },
        }, headers={'Authorization': access_token})
        # 似乎不需要replace \\
        r: dict = json.loads(resp.text)
        receive_data = []  #
        if str(r["status"]) == "200":
            receive_data: list = json.loads(r["payload"])["content"]
            print(f"获取录音记录列表成功, 录音列表: {receive_data}, 共 [{len(receive_data)}]条记录")
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


# TODO 获取业务数据
def request_business_data(phone: str = '', start_time: str = '', end_time: str = '', business_type: str = '',
                          agent_name: str = '') -> list:
    """
    请求语音质检接口
    根据 客户号码, 通话时间, 坐席ID, 业务类型来获取业务数据, 并追加到通话记录数据中
    :param start_time: 通话开始时间 格式: yyyy-mm-dd
    :param end_time:  通话结束时间 格式: yyyy-mm-dd
    :param phone:
    :param business_type: 共三种 客服：CUSTOMER_SERVICE, 信审：CREDIT_REVIEW, 催收：COLLECTION
    :param agent_name: 坐席姓名
    :return:
    """
    qc_url = 'http://open.csleasing.com.cn/uop/ecar/v1/voice/queryVoice'
    try:
        resp = httpx.post(qc_url, json={
            'phoneNo': phone,
            'businessType': business_type,
            'customerServiceName': agent_name,
            'dialBeginDate': start_time,
            'dialEndDate': end_time
        })

        result = json.loads(resp.text)
        print('原始内容', result)
        if result['respCode'] == '0000':
            business_data: list[dict] = result['data']['voiceQualityInspectionList']
            # print(f"获取录音质检业务数据成功, 录音数据: {str(business_data)}")
        else:
            business_data = []
            print(f"接口返回了错误的状态码, 状态码: {result['respCode']}, 状态错误提示: {result['respMsg']}")
    except Exception as exc:
        print(f'获取录音质检业务数据失败, 请确认接口通信是否正常. \n错误提示: {exc}')
        business_data = []

    return business_data


if __name__ == '__main__':
    # data_list = request_record_data(start_date='2021-10-05 00:00:00',
    #                     end_date='2021-10-05 23:59:59')
    # print(data_list)
    # 查询测试数据
    # 客服
    business_data1 = request_business_data(phone='15038311797',
                                           start_time='2022-04-13',
                                           end_time='2022-04-13',
                                           business_type='CREDIT_REVIEW',
                                           agent_name='赵亚飞')

    print(business_data1)



