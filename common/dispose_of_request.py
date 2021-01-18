"""
#-*- coding: utf-8 -*-

Created on 2021/1/10 17:50

@author: LT
"""
import os
import json
from api_format import ContentTypeDisposition, Data, Headers
import api_functions
import api_relogic  # 重构了逻辑函数
import logging
import pprint
import requests

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
    body = Data()   # 这个实例里包含每个特定api操作的要求格式

    # TODO: 先post请求getalldevicestype以获得内容，再用厂家名、CT、PT正则匹配得出结果
    getalldevicetypes = ContentTypeDisposition(headers_=headers.headers_query_templates)  # 这个请求不需要带请求体
    getalldevicetypes_res = getalldevicetypes.request_method_edge_getalldevicetypes()
    templates = []
    if getalldevicetypes_res.json()['retCode'] == 10000:
        print('模板信息获得成功！')
        for elem in getalldevicetypes_res.json()['data']:
            templates.append((elem['id'], elem['deviceName']))  # 把每个模板名与其对应的id形成一个元组放到列表中
        print(templates)
    else:
        print('模板信息获得失败！错误代码是：')
        print(getalldevicetypes_res.json())
        raise Exception('变比模板获得失败！')

    for each_station in origin_data:
        STATION = each_station['站名']    # 站点名字
        siteID = each_station['siteID']     # 每个站点的siteID
        ADDRESS = each_station['address']   # 站点对应的地址
        EXCEL_ID = each_station['excelid']  # 站点对应的excel_id
        SYNCHRONIZE_DICT = {
            'station_name': STATION,
            'address': ADDRESS,
            'site_id': siteID,
            'excel_id': EXCEL_ID,
        }   # 这个字典是用于后期同步的
        SYNCHRONIZE_DICT.setdefault('devices_list', None)

        exp = ContentTypeDisposition(body.edge_getallboxinfo(siteID), headers.headers_multipart)  # 创建getallboxinfo的请求体的实例
        st = exp.request_method_edge_getallboxinfo()     # 获得Edge中的盒子信息
        if len(st.json()['data']) == 0:
            print('该场站下没有盒子')
            # 往场站信息里添加盒子
            new_list = api_relogic.add_devices_in_station_info(siteID, each_station, body, headers, logging)

            # 去到Edge接入中新建盒子
            box_set = set([(elem['ip'], elem['sn']) for elem in new_list])  # 现在box_set是个集合类型
            api_relogic.add_boxes_in_egde_access(siteID, body, headers, box_set, logging)   # 已新建完盒子

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
                            value['collectId'] = collect['id']  # 给new_list新添加一对键值对
                else:
                    # 已建立过的，则直接获取collectId
                    getallboxinfo = ContentTypeDisposition(body.edge_getallboxinfo(siteID), headers.headers_multipart)
                    getallboxinfo_res = getallboxinfo.request_method_edge_getallboxinfo()
                    for collect in getallboxinfo_res.json()['data'][0]['collectList']:
                        if collect['attributes']['connIP'].endswith(value['portnum']):
                            value['collectId'] = collect['id']  # 新添加一对键值对
            pprint.pprint(new_list)     # 这个时候的new_list比较完全了
            # 连接添加完后开始选中已添加的设备
            for each_kit in new_list:
                result = api_functions.which_template(templates, each_kit['manufacturer'], each_kit['CT'], each_kit['PT'])
                if result == 'failed':
                    result = '4114'     # 匹配失败的话，就默认用 4114 温州电管家104转发YC78这个模板
                    logging.warning(f"站名：{STATION}，siteID：{siteID},它的- {each_kit['name']} -模板匹配失败！已选成默认模板")
                adddevices = ContentTypeDisposition(
                    body.edge_adddevices(siteID, each_kit['sn'], each_kit['objectID'], each_kit['collectId'],
                                         each_kit['modbus'], each_kit['manufacturer'], result), headers.headers_json)
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

            # 发布完后就是要去做拓扑结构的导入了
            SYNCHRONIZE_DICT['devices_list'] = new_list     # 首先把对应的设备字典填入同步字典
            response = api_functions.synchronize_topo(SYNCHRONIZE_DICT)    # 把同步的事情全权交给函数处理
            if str(response['code']) == '1':
                print('模板上传成功！')
            else:
                print('模板上传失败，错误代码是：')
                print(response)
            sy = requests.get(f'http://122.228.156.194:8081/backend/platform/common/initMdmidBySite?siteId={siteID}')
            if str(sy.json()['code']) == '1':
                print('同步成功')
            else:
                print('同步失败，错误代码是：')
                print(sy.json())

        else:
            print('该场站下有盒子')
            # TODO: 首先getallboxinfo，因为有盒子了嘛，然后去找其下的端口号——注意端口号只于连接有关，与盒子无关，故是去判断连接！！！
            if len(st.json()['data'][0]['collectList']) == 0:    # 说明盒子下无连接，则可以直接往场站信息中添加设备，然后后续操作
                # 往场站信息里添加盒子，添加完成后返回了设备的信息
                new_list = api_relogic.add_devices_in_station_info(siteID, each_station, body, headers, logging)

                # TODO: 场站信息里添加完设备之后，就开始Edge接入等——连接名从104转发1开始
                already_exists_sn_list = [each_sn['boxSN'] for each_sn in st.json()['data']]  # 获得已有的盒子sn号列表
                box_set = set([(elem['ip'], elem['sn']) for elem in new_list])  # 现在box_set是个集合类型
                api_relogic.add_boxes_in_egde_access(
                    siteID, body, headers, box_set, logging, already_exists_sn_list=already_exists_sn_list)

            else:   # 说明有连接，则去遍历连接，查看有无对应的端口号——连接名需要获得已有连接数量来变化
                # 获得连接下的所有端口号的列表，函数会判断是否跳过已重复的端口号的设备
                collect_portnum_list = [each_collect['attributes']['connIP'][-5:] for each_collect in st.json()['data'][0]['collectList']]
                new_list = api_relogic.add_devices_in_station_info(
                    siteID, each_station, body, headers, logging, collect_portnum_list=collect_portnum_list)

                # TODO: 2.1遍历查看Edge接入中无对应的SN号盒子
                already_exists_sn_list = [each_sn['boxSN'] for each_sn in st.json()['data']]    # 获得已有的盒子sn号列表
                box_set = set([(elem['ip'], elem['sn']) for elem in new_list])  # 现在box_set是个集合类型
                #
                api_relogic.add_boxes_in_egde_access(
                    siteID, body, headers, box_set, logging, already_exists_sn_list=already_exists_sn_list)

                # TODO: 2.1.1若无，则去到Edge接入中新建盒子、新建连接（连接名字用遍历连接数+1来获得）、选设备及模板、最后点击发布

                # TODO: 2.1.2若有，则去到Edge接入中对应的盒子下、新建连接（连接名字用遍历连接数+1来获得）、选设备及模板、最后点击发布

logging.info('End of Program')
