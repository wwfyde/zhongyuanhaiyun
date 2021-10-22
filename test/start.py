"""
连接接口测试

"""

import httpx

url: str = 'http://gateway.clmp-uat.csleasing.com.cn/hitf/V1/rest/invoke?namespace=HZERO&serverCode=CCUZ.CENTER.CALL' \
      '&interfaceCode=clmp-customize.udeskcallcentercalllog.queryAllType'

print(url)
data: dict = {

}
r = httpx.post(url=url, json=data)