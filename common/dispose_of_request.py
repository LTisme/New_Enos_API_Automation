"""
#-*- coding: utf-8 -*-

Created on 2021/1/10 17:50

@author: LT
"""
import os
import json
from api_format import ContentTypeDisposition, Data, Headers
import logging
from time import sleep

import pprint

logging.basicConfig(filename='api_logging.log', level=logging.DEBUG,
                    format='%(asctime)s - [line:%(lineno)d] - %(levelname)s - %(message)s')
logging.info('Start of Program')

os.chdir(os.path.dirname(os.path.realpath(__file__)))
with open('data.json', encoding='UTF-8') as fbj:
    origin_data = json.load(fbj)      # 现在data就是想要的数据结构

# headers 和 data 样例
# headers = {
#     'content-type': 'multipart/form-data; boundary=----WebKitFormBoundary3wf0kPKxFBnmf0gQ'
# }
#
# data = {
#     "parentid": '253aa2b2cc006000',     # 即删试验站 的 siteID
#     "grouptype": "true",
# }


if __name__ == '__main__':
    headers = Headers()
    body = Data()
    for each_station in origin_data:
        STATION = each_station['站名']    # 站点名字
        siteID = each_station['siteID']     # 每个站点的siteID

        exp = ContentTypeDisposition(body.edge_getallboxinfo(siteID), headers.headers_multipart)  # 创建getallboxinfo的请求体的实例
        st = exp.request_method_edge_getallboxinfo()     # 获得Edge中的盒子信息
        if len(st.json()['data']) == 0:
            print('该场站下没有盒子')
            # 去往场站信息中添加设备，并获得每个新添加的设备的objectID
            # 需要先请求一次childdetail来获得新旧设备以防止残留设备与已有设备名字重名带来的objectID无法区分
            childdetail = ContentTypeDisposition(body.station_childdetail(siteID), headers.headers_multipart)
            childdetail_res = childdetail.request_method_stationdetail_childdetail()
            projid = childdetail_res.json()['data'][0]['objectID']  # 获得重要的projid
            catid = childdetail_res.json()['data'][0]['categoryIDs'][0]
            print('projid is ' + projid)
            # TODO: 1请求childdetailpagestep
            childdetailpagestep = ContentTypeDisposition(body.station_childdetailpagestep(projid), headers.headers_multipart)
            childdetailpagestep_res = childdetailpagestep.request_method_stationdetail_childdetailpagestep()
            if len(childdetailpagestep_res.json()['data']['data']) == 0:
                # TODO: 1.1若设备数为零，说明没有残留设备，创建一个空列表，每adddevice后，post一次childdetailpagestep,将获得的新objectID放进空列表中
                print(' 这个场站下没有残留设备')
                old_list = []
            else:
                # TODO: 1.2若设备数不零，说明有残留设备，创建一个空列表，将已有设备的objectID放入列表，
                #  然后每adddevice后post一次childdetailpagestep并与旧列表比对，将新ID作为新添设备的额外属性
                print(' 这个场站下有残留设备，请检查是否需要删除')
                old_list = []
                for val in childdetailpagestep_res.json()['data']['data']:
                    old_list.append(val['objectID'])
                print('oldlist is ', old_list)
                # 后续需要删除这个，这是因为adddevice后
            for each_device in each_station['信息']:
                PORT_NUM = str(each_device['port_num'])  # 获得了端口号
                KitName = str(each_device['device_name'])  # 设备名
                Capacity = str(each_device['capacity'])  # 容量
                RatedCurrent = str(each_device['rated_current'])  # 额定电流
                DEVICE_CT = str(each_device['CT'])  # CT
                DEVICE_PT = str(each_device['PT'])  # PT
                DEVICE_MANUFACTURER = str(each_device['manufacturer'])
                LOGIC_NUM = str(each_device['modbus'])  # 获得了对应的公共地址，即逻辑编号
                adddevice = ContentTypeDisposition(body.station_adddevice(projid, catid, KitName, RatedCurrent,
                                                                          Capacity, siteID), headers.headers_multipart)
                adddevice_res = adddevice.request_method_stationdetail_adddevice()
                print('添加设备后返回的内容：')
                print(adddevice_res.json())
                if adddevice_res.json()['data'] is True:
                    print('添加设备成功！')
                else:
                    print('添加设备失败！')

            # TODO: 去到Edge接入中新建盒子、新建连接（连接名字从104转发1开始算）、选设备及模板、最后点击发布
        else:
            print('该场站下有盒子')
            # 需要先请求一次childdetail来获得新旧设备以防止残留设备与已有设备名字重名带来的objectID无法区分
            childdetail = ContentTypeDisposition(body.station_childdetail(siteID), headers.headers_multipart)
            childdetail_res = childdetail.request_method_stationdetail_childdetail()
            projid = childdetail_res.json()['data'][0]['objectID']  # 获得重要的projid
            catid = childdetail_res.json()['data'][0]['categoryIDs'][0]
            print('projid is ' + projid)
            # TODO: 1遍历所有盒子查看盒子下有无对应的端口号，若有则记录到日志中，让人手动去查具体情况；

            # TODO: 2遍历所有盒子查看盒子下有无对应的端口号，若无则去往场站信息中添加设备，并获得每个新添加的设备的objectID

            # TODO: 2.1查看Edge接入中无对应的SN号盒子

            # TODO: 2.1.1若无，则去到Edge接入中新建盒子、新建连接（连接名字用遍历连接数+1来获得）、选设备及模板、最后点击发布

            # TODO: 2.1.2若有，则去到Edge接入中对应的盒子下、新建连接（连接名字用遍历连接数+1来获得）、选设备及模板、最后点击发布
        for each_device in each_station['信息']:
            PORT_NUM = str(each_device['port_num'])  # 获得了端口号
            KitName = str(each_device['device_name'])  # 设备名
            Capacity = str(each_device['capacity'])  # 容量
            RatedCurrent = str(each_device['rated_current'])  # 额定电流
            DEVICE_CT = str(each_device['CT'])  # CT
            DEVICE_PT = str(each_device['PT'])  # PT
            DEVICE_MANUFACTURER = str(each_device['manufacturer'])
            LOGIC_NUM = str(each_device['modbus'])  # 获得了对应的公共地址，即逻辑编号

    # # 场站信息中添加设备
    # exp = ContentTypeDisposition(data, headers)     # 创建一个multipart/form-data头的实例
    # st = exp.request_method_stationdetail_childdetail()     # 场站信息中——添加设备前获取必要信息的操作
    # # 判断场站是——已有设备的还是无设备的
    # data = {
    #     "pagesize": 10,
    #     "type": 0,
    #     "pivot": 'null',
    #     "attr": {"parentid": st.json()['data'][0]['objectID'], "name": ""}  # 这个parentID是projid！！！！！！
    # }
    # exp3 = ContentTypeDisposition(data, headers)
    # st = exp3.request_method_stationdetail_childdetailpagestep()
    # if len(st.json()['data']['data']) == 0:
    #     print('这个场站没有设备')
    # else:
    #     print('这个场站已有设备')
    #
    # data = {    # data里的设备名、Un、maxCurrent、TransformerCapacity、siteID等都是需要从Excel里读取的
    #     "projid": st.json()['data'][0]['objectID'],
    #     "catid": st.json()['data'][0]['categoryIDs'][0],
    #     "attr": {"name.default": "又是一个新设备", "name.zh-CN": "又是一个新设备", "Un": "23123", "maxCurrent": "234234",
    #              "TransformerCapacity": "32434", "model": "-1", "typeId": "227", "typeName": "多功能电表", "innerVer": "-1",
    #              "inputer": "shujun.wu", "isAttachedSite": "false", "siteID": "253aa2b2cc006000"}
    # }       # 创建一个设备信息字典
    # exp2 = ContentTypeDisposition(data, headers)
    # st = exp2.request_method_stationdetail_adddevice()
    # if str(st.json()['retCode']) == '10000':
    #     print('设备添加成功')
    # else:
    #     print('设备添加失败')
    #
    # # 设备添加完后需要再post一下childdetailpagestep来获得每个设备的objectID，这是后面连接中添加设备选取的唯一ID
    # # 但这样无法区分同名字的设备，应该每添加一个设备就
    # data = {
    #     "pagesize": 10,
    #     "type": 0,
    #     "pivot": 'null',
    #     "attr": {"parentid": "253aa2b30e002000", "name": ""}    # 这个parentID是projid！！！！！！
    # }
    # exp3 = ContentTypeDisposition(data, headers)
    # st = exp3.request_method_stationdetail_childdetailpagestep()
    # deviceIDName = []
    # for value in st.json()['data']['data']:
    #     device_name = value['detailInfo']['name']
    #     device_id = value['detailInfo']['objectID']
    #     device_isattachedsite = value['detailInfo']['isAttachedSite']
    #     deviceIDName.append({'name': device_name, 'id': device_id, 'attached?': device_isattachedsite})     # 这样就把每个设备名与其ID号绑在一起并放到列表中
    #
    # pprint.pprint(deviceIDName)
    #
    # # TODO: 在Edge连接中添加盒子
logging.info('End of Program')
