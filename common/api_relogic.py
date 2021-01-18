"""
#-*- coding: utf-8 -*-

Created on 2021/1/17 17:47

@author: LT
"""
from api_format import ContentTypeDisposition
import pprint
import api_functions


def add_devices_in_station_info(siteID, station_dict, body, headers, logging, collect_portnum_list=[]):
    """
    往场站信息里添加设备的函数
    :param siteID: 站点对应的siteID
    :param station_dict: 站点字典
    :param body: 请求体实例
    :param headers: 请求头实例
    :param logging: 日志模块
    :param collect_portnum_list: 当对应站点下已有盒子与连接时才会传入的已有的端口号列表，否则默认为空列表
    :return: list 后面很有用的各站点详细信息
    """
    if not collect_portnum_list:
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

        return new_list     # 当然，全部添加失败，导致列表为空也是可能的，不过应该发生不了
    else:
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
    if not already_exists_sn_list:
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
    else:
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
                    logging.warning(f'{boxname}  添加失败，失败代码为：{str(addbox_res.json())}')
