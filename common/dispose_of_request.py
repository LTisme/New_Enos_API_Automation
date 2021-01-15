"""
#-*- coding: utf-8 -*-

Created on 2021/1/10 17:50

@author: LT
"""
import os
import json
from api_format import ContentTypeDisposition, Data, Headers
import api_functions
import logging
import pprint

logging.basicConfig(filename='api_logging.log', level=logging.DEBUG,
                    format='%(asctime)s - [line:%(lineno)d] - %(levelname)s - %(message)s')
logging.info('Start of Program')

os.chdir(os.path.dirname(os.path.realpath(__file__)))
api_functions.extract_data_into_a_json()    # 读取data.xlsx里的数据，并生成data.json格式的文件
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
    body = Data()   # 这个示例里包含每个特定api操作的要求格式
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
                print(' 这个场站没有盒子但有残留设备，请检查是否需要删除')
                old_list = []
                for val in childdetailpagestep_res.json()['data']['data']:
                    old_list.append(val['objectID'])
                print('oldlist is ', old_list)
            new_list = []   # 这个列表用来存储新增设备的各个属性，这样就绝对不会因为重名搞混objectID，已测试通过
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
                # 每次添加一个设备需要post一次childdetailpagestep以获得设备对应的objectID
                childdetailpagestep_res = childdetailpagestep.request_method_stationdetail_childdetailpagestep()
                for val in childdetailpagestep_res.json()['data']['data']:
                    if val['objectID'] not in old_list:     # 找到新增设备的objectID
                        ip, sn = api_functions.judgement(PORT_NUM)
                        new_list.append({'name': KitName, 'objectID': val['objectID'], 'CT': DEVICE_CT, 'PT': DEVICE_PT,
                                         'modbus': LOGIC_NUM, 'manufacturer': DEVICE_MANUFACTURER, 'portnum': PORT_NUM,
                                         'ip': ip, 'sn': sn})
                        # 将objectID与后续必要信息其记录到new_list中
                        old_list.append(val['objectID'])    # 并将它放进old_list中
                if adddevice_res.json()['data'] is True:    # 这对ifelse可以注释掉或者删掉
                    print('添加设备成功！')
                else:
                    print('添加设备失败！')
            pprint.pprint(new_list)

            # TODO: 去到Edge接入中新建盒子、新建连接（连接名字从104转发1开始算）、选设备及模板、最后点击发布
            # 用set的办法来将port_list里删除重复项
            box_set = set([(elem['ip'], elem['sn']) for elem in new_list])     # 现在box_set是个集合类型
            for elem in box_set:   # 每个elem是一个元组
                boxname = elem[0] + '盒子'
                sn = elem[1]
                addbox = ContentTypeDisposition(body.edge_addbox(siteID, boxname, sn), headers.headers_json)  # 这个用json
                print('\n\n')
                print(body.edge_addbox(siteID, boxname, sn))
                addbox_res = addbox.request_method_edge_addbox()
                if addbox_res.json()['retCode'] == 10000:
                    print(boxname + ' 添加成功')
                else:
                    print(boxname + ' 添加失败，失败代码为：')
                    print(addbox_res.json())

            # 添加完盒子后需要开始添加所有连接，需要端口号筛重
            port_set = set([elem['portnum'] for elem in new_list])  # 现在port_set中含有不重复的端口号
            support_list = []
            temp_collect = ""
            for value in new_list:
                linke_name = api_functions.which_link(value['portnum'], support_list)
                if temp_collect != linke_name:  # 检测此连接是否已建立过，已建立过的跳过不建
                    temp_collect = linke_name
                    addcollect = ContentTypeDisposition(
                        body.edge_addcollect(siteID, linke_name, value['ip'], value['portnum']),
                        headers.headers_multipart)
                    addcollect_res = addcollect.request_method_edge_addcollect()    # 请求添加一个连接
                    if addcollect_res.json()['retCode'] == 10000:
                        print(f'{linke_name}-连接添加成功！')
                    else:
                        print(f'{linke_name}-连接添加失败！失败代码是：')
                        print(addcollect_res.json())
                    # 每添加一个连接后需要获得其collectID,然后放入new_list中，作为有一个额外属性
                    getallboxinfo = ContentTypeDisposition(body.edge_getallboxinfo(siteID), headers.headers_multipart)
                    getallboxinfo_res = getallboxinfo.request_method_edge_getallboxinfo()
                    for collect in getallboxinfo_res.json()['data'][0]['collectList']:
                        if collect['attributes']['connIP'].endswith(value['portnum']):
                            value['collectId'] = collect['id']  # 新添加一对键值对
                else:
                    # 已建立过的，则直接获取collectId
                    getallboxinfo = ContentTypeDisposition(body.edge_getallboxinfo(siteID), headers.headers_multipart)
                    getallboxinfo_res = getallboxinfo.request_method_edge_getallboxinfo()
                    for collect in getallboxinfo_res.json()['data'][0]['collectList']:
                        if collect['attributes']['connIP'].endswith(value['portnum']):
                            value['collectId'] = collect['id']  # 新添加一对键值对
            pprint.pprint(new_list)     # 这个时候的new_list比较完全了
            # 开始选中已添加的设备
            for each_kit in new_list:
                adddevices = ContentTypeDisposition(
                    body.edge_adddevices(siteID, each_kit['sn'], each_kit['objectID'], each_kit['collectId'],
                                         each_kit['modbus'], each_kit['manufacturer']), headers.headers_json)
                adddevices_res = adddevices.request_method_edge_adddevices()
                if adddevices_res.json()['retCode'] == 10000:
                    print(f'{each_kit["name"]}-设备已添到对应连接！')
                else:
                    print(f'{each_kit["name"]}-设备选中失败！错误码是：')
                    print(adddevices_res.json())

            # 发布盒子
            for each_box in box_set:
                publishbox = ContentTypeDisposition(body.edge_publishbox(siteID, each_box[1]), headers.headers_multipart)
                publishbox_res = publishbox.request_method_edge_publishbox()
                if publishbox_res.json()['retCode'] == 10000:
                    print(f'{each_box[0]}-盒子发布成功！')
                else:
                    print(f'{each_box[0]}-盒子发布失败！错误代码是：')
                    print(publishbox_res.json())

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

    # TODO: 在Edge连接中添加盒子
logging.info('End of Program')
