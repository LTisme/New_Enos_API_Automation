"""
#-*- coding: utf-8 -*-

Created on 2021/1/17 17:47

@author: LT
"""
from api_format import ContentTypeDisposition
import pprint
import api_functions
import requests


def get_all_devices_type(headers, logging):
    """
    获得变比模板与其对应的值
    :param headers: 请求头
    :param logging: 日志模块
    :return: 变比模板与其对应的值的元组列表
    """
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
        logging.warning(f"模板信息获得失败！错误代码是：{str(getalldevicetypes_res.json())}")
        raise Exception('变比模板获得失败！')
    return templates


def add_devices_in_station_info(siteID, station_dict, body, headers, logging, collect_portnum_list=[]):
    """
    往场站信息里添加设备的函数，可以判断是否已有重复的端口号
    :param siteID: 站点对应的siteID
    :param station_dict: 站点字典
    :param body: 请求体实例
    :param headers: 请求头实例
    :param logging: 日志模块
    :param collect_portnum_list: 当对应站点下已有盒子与连接时才会传入的已有的端口号列表，否则默认为空列表，用来查重已有端口号的
    :return: list 后面很有用的各站点详细信息；当然，全部添加失败，导致列表为空也是可能的，全空就需要外界判断了！！！
    """
    if not collect_portnum_list:    # 没有需要对比端口号的残留连接
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
        new_list = []   # 这个列表用来存储新增设备的各个属性，这样就绝对不会因为重名搞混objectID，已测试通过
        old_list = []   # 创建一个空列表，每adddevice后，post一次childdetailpagestep,将获得的新objectID放进空列表中
        if len(childdetailpagestep_res.json()['data']['data']) == 0:
            # 若设备数为零，说明无残留设备
            print(' 这个场站下没有残留设备')
        else:
            # 若设备数不为零，说明有残留设备
            print(' 这个场站没有盒子但有残留设备，请检查是否需要删除')
            logging.warning(f'这个siteid的站点{siteID}的场站信息中有残留设备，请检查！')
            for val in childdetailpagestep_res.json()['data']['data']:
                old_list.append(val['objectID'])
            # print('oldlist is ', old_list)
        for each_device in station_dict['信息']:
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
            if adddevice_res.json()['data'] is True:
                print('添加设备成功！')
                # 每次添加一个设备需要post一次childdetailpagestep以获得设备对应的objectID
                childdetailpagestep_res = childdetailpagestep.request_method_stationdetail_childdetailpagestep()
                for val in childdetailpagestep_res.json()['data']['data']:
                    if val['objectID'] not in old_list:  # 找到新增设备的objectID
                        ip, sn = api_functions.judgement(PORT_NUM)
                        new_list.append({'name': KitName, 'objectID': val['objectID'], 'CT': DEVICE_CT, 'PT': DEVICE_PT,
                                         'modbus': LOGIC_NUM, 'manufacturer': DEVICE_MANUFACTURER, 'portnum': PORT_NUM,
                                         'ip': ip, 'sn': sn})
                        # 将objectID与后续必要信息其记录到new_list中
                        old_list.append(val['objectID'])  # 并将它放进old_list中
            else:
                print('添加设备失败！')
                logging.warning(f'这个siteid的站点{siteID}的{KitName}设备因添加失败而被略过！')
                continue    # 跳过此设备，不被录入到new_list里面

        pprint.pprint(new_list)     # 不想看它的结构可以注释掉

        return new_list
    else:   # 有需要对比端口号的残留连接
        # 去往场站信息中添加设备，并获得每个新添加的设备的objectID
        # 需要先请求一次childdetail来获得新旧设备以防止残留设备与已有设备名字重名带来的objectID无法区分
        childdetail = ContentTypeDisposition(body.station_childdetail(siteID), headers.headers_multipart)
        childdetail_res = childdetail.request_method_stationdetail_childdetail()
        projid = childdetail_res.json()['data'][0]['objectID']  # 获得重要的projid
        catid = childdetail_res.json()['data'][0]['categoryIDs'][0]
        print('projid is ' + projid)
        # TODO: 1请求childdetailpagestep
        childdetailpagestep = ContentTypeDisposition(body.station_childdetailpagestep(projid),
                                                     headers.headers_multipart)
        childdetailpagestep_res = childdetailpagestep.request_method_stationdetail_childdetailpagestep()
        new_list = []  # 这个列表用来存储新增设备的各个属性，这样就绝对不会因为重名搞混objectID，已测试通过
        old_list = []  # 创建一个空列表，每adddevice后，post一次childdetailpagestep,将获得的新objectID放进空列表中
        if len(childdetailpagestep_res.json()['data']['data']) == 0:
            # 若设备数为零，说明无残留设备
            print(' 这个场站下没有残留设备')
        else:
            # 若设备数不为零，说明有残留设备
            print(' 这个场站没有盒子但有残留设备，请检查是否需要删除')
            logging.warning(f'这个siteid的站点{siteID}的场站信息中有残留设备，请检查！')
            for val in childdetailpagestep_res.json()['data']['data']:
                old_list.append(val['objectID'])
            # print('oldlist is ', old_list)
        for each_device in station_dict['信息']:
            PORT_NUM = str(each_device['port_num'])  # 获得了端口号
            if PORT_NUM in collect_portnum_list:  # 说明这个端口号站点已经有了
                print(f'siteid:{siteID}站点的{PORT_NUM}端口号已存在！')
                logging.warning(f'siteid:{siteID}站点的{PORT_NUM}端口号已存在！请检查！')
                continue  # 跳过这个设备，不做
            else:  # 这个端口号对应场站还未有端口号，可以
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
                if adddevice_res.json()['data'] is True:
                    print('添加设备成功！')
                    # 每次添加一个设备需要post一次childdetailpagestep以获得设备对应的objectID
                    childdetailpagestep_res = childdetailpagestep.request_method_stationdetail_childdetailpagestep()
                    for val in childdetailpagestep_res.json()['data']['data']:
                        if val['objectID'] not in old_list:  # 找到新增设备的objectID
                            ip, sn = api_functions.judgement(PORT_NUM)
                            new_list.append({'name': KitName, 'objectID': val['objectID'], 'CT': DEVICE_CT, 'PT': DEVICE_PT,
                                             'modbus': LOGIC_NUM, 'manufacturer': DEVICE_MANUFACTURER, 'portnum': PORT_NUM,
                                             'ip': ip, 'sn': sn})
                            # 将objectID与后续必要信息其记录到new_list中
                            old_list.append(val['objectID'])  # 并将它放进old_list中
                else:
                    print('添加设备失败！')
                    logging.warning(f'这个siteid的站点{siteID}的{KitName}设备因添加失败而被略过！')
                    continue  # 跳过此设备，不被录入到new_list里面

        pprint.pprint(new_list)  # 不想看它的结构可以注释掉

        return new_list  # 当然，全部添加失败，导致列表为空也是可能的，不过应该发生不了


def add_boxes_in_egde_access(siteID, body, headers, box_set, logging, already_exists_sn_list=[]):
    """
    可以判定是否已有sn号，可以新建盒子并防止盒子sn号冲突的函数
    :param siteID: 站点的siteID
    :param body: 请求体
    :param headers: 请求头
    :param box_set: 盒子sn号集合
    :param logging: 日志模块
    :param already_exists_sn_list: 获取到的页面已有的sn号列表
    :return: 无返回值
    """
    if not already_exists_sn_list:  # 如果未传入此列表
        for elem in box_set:  # 每个elem是一个元组
            boxname = elem[0] + '盒子'
            sn = elem[1]
            addbox = ContentTypeDisposition(body.edge_addbox(siteID, boxname, sn), headers.headers_json)  # 这个用json
            addbox_res = addbox.request_method_edge_addbox()
            if addbox_res.json()['retCode'] == 10000:
                print(boxname + ' 添加成功!')
            else:
                print(boxname + ' 添加失败!')
                logging.warning(f'{boxname}  添加失败，失败代码为：{str(addbox_res.json())}')
    else:   # 如果传入了此列表
        for elem in box_set:  # 每个elem是一个元组
            if elem[1] in already_exists_sn_list:  # 若sn号已有，则可以不建这个盒子
                logging.info(f'这个{elem[1]}sn号的盒子已有，跳过不建')
                continue    # 跳过新建这个sn号的盒子，因为已经有了
            else:
                boxname = elem[0] + '盒子'
                sn = elem[1]
                addbox = ContentTypeDisposition(body.edge_addbox(siteID, boxname, sn), headers.headers_json)  # 这个用json
                addbox_res = addbox.request_method_edge_addbox()
                if addbox_res.json()['retCode'] == 10000:
                    print(boxname + ' 添加成功!')
                else:
                    print(boxname + ' 添加失败!')
                    logging.warning(f'{boxname}  添加失败，失败代码为：{str(addbox_res.json())}')  # 致命错误！


def add_collects_in_edge_access(siteID, body, headers, new_list, logging, startnum=0):
    """
    edge接入中添加完盒子后建立连接的函数
    :param siteID: 站点的siteid
    :param body: 请求体
    :param headers: 请求头
    :param new_list: 设备各属性列表
    :param logging: 日志模块
    :param startnum: 连接名后缀基值
    :return: 无返回值
    """
    support_list = []
    temp_collect = ""   # 暂存连接名
    for value in new_list:
        linke_name = api_functions.which_link(value['portnum'], support_list, startnum)
        if temp_collect != linke_name:  # 检测此连接是否已建立过，已建立过的跳过不建
            temp_collect = linke_name
            addcollect = ContentTypeDisposition(
                body.edge_addcollect(siteID, linke_name, value['ip'], value['portnum']),
                headers.headers_multipart)
            addcollect_res = addcollect.request_method_edge_addcollect()  # 请求添加一个连接
            if addcollect_res.json()['retCode'] == 10000:
                print(f'{linke_name}-连接添加成功！')
            else:
                print(f'{linke_name}-连接添加失败！')
                logging.warning(f'{linke_name}-连接添加失败！失败代码是：\n{str(addcollect_res.json())}')    # 这应该是个致命错误
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
    pprint.pprint(new_list)  # 这个时候的new_list比较完全了，因为添加了连接的id号


def select_devices_to_corresponding_collect_in_edge_access(siteID, body, headers, new_list, templates, logging):
    """
    连接建立后将设备勾选到对应的连接下的函数
    :param siteID: 站点的siteid
    :param body: 请求体
    :param headers: 请求头
    :param new_list: 设备各属性列表
    :param templates: 最新的模板值信息
    :param logging: 日志模块
    :return: 无返回值
    """
    for each_kit in new_list:
        # 开始选择模板
        result = api_functions.which_template(templates, each_kit['manufacturer'], each_kit['CT'], each_kit['PT'])
        if result == 'failed':
            result = '4114'  # 匹配失败的话，就默认用 4114 温州电管家104转发YC78这个模板
            logging.warning(f"siteID：{siteID},它的- {each_kit['name']} -模板匹配失败！已选成默认模板")
        adddevices = ContentTypeDisposition(
            body.edge_adddevices(siteID, each_kit['sn'], each_kit['objectID'], each_kit['collectId'],
                                 each_kit['modbus'], each_kit['manufacturer'], result), headers.headers_json)
        adddevices_res = adddevices.request_method_edge_adddevices()
        if adddevices_res.json()['retCode'] == 10000:
            print(f'{each_kit["name"]}-设备已添到对应连接！')
        else:
            print(f'{each_kit["name"]}-设备选中失败！错误码是：')
            logging.warning(f'{each_kit["name"]}-设备选中失败！错误码是：{adddevices_res.json()}')  # 致命错误，需要引起异常


def publish_sn_in_edge_access(siteID, body, headers, box_set, logging):
    """
    发布各个sn号的盒子的函数
    :param siteID: 站点siteid
    :param body: 请求体
    :param headers: 请求头
    :param box_set: sn号集合
    :param logging: 日志模块
    :return: 无返回值
    """
    for each_box in box_set:
        publishbox = ContentTypeDisposition(body.edge_publishbox(siteID, each_box[1]), headers.headers_multipart)
        publishbox_res = publishbox.request_method_edge_publishbox()
        if publishbox_res.json()['retCode'] == 10000:
            print(f'{each_box[0]}-盒子发布成功！')
        else:
            print(f'{each_box[0]}-盒子发布失败！错误代码是：')
            logging.warning(f'{each_box[0]}-盒子发布失败！错误代码是：{str(publishbox_res.json())}')


def synchronize_corresponding_station_with_template(siteID, synchronize_dict, logging):
    response = api_functions.synchronize_topo(synchronize_dict)  # 把同步的事情全权交给函数处理
    if str(response['code']) == '1':
        print('模板上传成功！')
    else:
        print('模板上传失败，错误代码是：')
        logging.warning(f'模板上传失败，错误代码是：{str(response.json())}')
    sc = requests.get(f'http://122.228.156.194:8081/backend/platform/common/initMdmidBySite?siteId={siteID}')
    if str(sc.json()['code']) == '1':
        print('同步成功')
    else:
        print('同步失败，错误代码是：')
        logging.warning(f"同步失败，错误代码是：{str(sc.json())}")
