"""
#-*- coding: utf-8 -*-

Created on 2021/1/14 12:32

@author: LT
"""
import os
import openpyxl
import pprint
import json


def extract_data_into_a_json():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    wb = openpyxl.load_workbook('data.xlsx')
    sht = wb['Sheet1']

    data_list = []      # 字典列表
    info_list = []      # 信息列表，后续还得根据情况是否需要新创建

    STATION = ""    # 用来暂存空站名前最新的站名
    STATION_ID = ""     # 用来存最新的站ID
    PORT = ""   # 用来存最新的端口号
    TEMP = ""   # 用来判断是否是同一个场站，它有一个暂存量的作用
    for row in range(2, sht.max_row + 1):       # 要包括进excel表里的最后一行
        """从里到外层层脱出"""
        if sht['C' + str(row)].value is not None and row >= 2 and sht['A' + str(row)].value is not None and\
                sht['J' + str(row)].value is not None:   # 如果设备名称不为空，站名不为空,端口号不为空
            STATION = sht['A' + str(row)].value     # 更新STATION
            STATION_ID = sht['B' + str(row)].value  # 更新STATION_ID
            PORT = sht['J' + str(row)].value        # 更新PORT
            device_name = sht['C' + str(row)].value     # 设备名
            modbus = sht['D' + str(row)].value      # 公共地址
            capacity = sht['E' + str(row)].value    # 容量
            rated_current = sht['F' + str(row)].value   # 额定电流
            CT = sht['G' + str(row)].value      # CT变比
            PT = sht['H' + str(row)].value      # PT变比
            manufacturer = sht['I' + str(row)].value    # 厂家名字
            port_num = sht['J' + str(row)].value    # 端口号
            # >>>>>>>>>>>>>>>>>>>>>>>基础信息分隔符
            site_ID = sht['B' + str(row)].value     # siteID
            station_name = sht['A' + str(row)].value    # 站点名字
            # >>>>>>>>>>>>>>>>>>>>>>>
            # 根据新信息创建一个新字典
            info_list_elem = {'device_name': device_name, 'modbus': modbus, 'capacity': capacity,
                              'rated_current': rated_current, 'CT': CT, 'PT': PT, 'manufacturer': manufacturer,
                              'port_num': port_num}  # 字典列表的字典元素中的信息列表中的元素
            if STATION != TEMP and TEMP != "":
                info_list = []
                info_list.append(info_list_elem)
            else:
                info_list.append(info_list_elem)
        elif sht['A' + str(row)].value is None and row <= sht.max_row:   # 若站名为空，且不大于最大行数
            if sht['J' + str(row)].value is not None:     # 如果站名为空，但端口号不为空
                PORT = sht['J' + str(row)].value    # 更新PORT
                device_name = sht['C' + str(row)].value     # 设备名
                modbus = sht['D' + str(row)].value  # 公共地址
                capacity = sht['E' + str(row)].value  # 容量
                rated_current = sht['F' + str(row)].value  # 额定电流
                CT = sht['G' + str(row)].value  # CT变比
                PT = sht['H' + str(row)].value  # PT变比
                manufacturer = sht['I' + str(row)].value  # 厂家名字
                port_num = sht['J' + str(row)].value  # 端口号
                # >>>>>>>>>>>>>>>>>>>>>>>基础信息分隔符
                site_ID = STATION_ID  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<则用STATION_ID替代siteID
                station_name = STATION  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<则用STATION替代站点名字
                # >>>>>>>>>>>>>>>>>>>>>>>
                # 根据新信息创建一个新字典
                info_list_elem = {'device_name': device_name, 'modbus': modbus, 'capacity': capacity,
                                  'rated_current': rated_current, 'CT': CT, 'PT': PT, 'manufacturer': manufacturer,
                                  'port_num': port_num}  # 字典列表的字典元素中的信息列表中的元素
                if STATION != TEMP and TEMP != "":
                    info_list = []
                    info_list.append(info_list_elem)
                else:
                    info_list.append(info_list_elem)
            elif sht['J' + str(row)].value is None:     # 如果站名为空，端口号也为空
                device_name = sht['C' + str(row)].value  # 设备名
                modbus = sht['D' + str(row)].value  # 公共地址
                capacity = sht['E' + str(row)].value  # 容量
                rated_current = sht['F' + str(row)].value  # 额定电流
                CT = sht['G' + str(row)].value  # CT变比
                PT = sht['H' + str(row)].value  # PT变比
                manufacturer = sht['I' + str(row)].value  # 厂家名字
                port_num = PORT  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<则用PORT代替端口号
                # >>>>>>>>>>>>>>>>>>>>>>>基础信息分隔符
                site_ID = STATION_ID  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<则用STATION_ID替代siteID
                station_name = STATION  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<则用STATION替代站点名字
                # >>>>>>>>>>>>>>>>>>>>>>>
                # 根据新信息创建一个新字典
                info_list_elem = {'device_name': device_name, 'modbus': modbus, 'capacity': capacity,
                                  'rated_current': rated_current, 'CT': CT, 'PT': PT, 'manufacturer': manufacturer,
                                  'port_num': port_num}  # 字典列表的字典元素中的信息列表中的元素
                if STATION != TEMP and TEMP != "":
                    info_list = []
                    info_list.append(info_list_elem)
                else:
                    info_list.append(info_list_elem)
        else:
            print("表头下无数据")

        # 层层脱出==============================================层层脱出
        if TEMP != STATION:
            TEMP = STATION
            data_list_elem = {"站名": STATION, "siteID": STATION_ID, "信息": info_list}  # 字典列表的字典元素
            data_list.append(data_list_elem)

    pprint.pprint(data_list)

    # 把结果保存为json文件

    with open('data.json', 'w', encoding='UTF-8') as file_obj:
        json.dump(data_list, file_obj, ensure_ascii=False)      # ensure_ascii=False 用来存储为真正的中文


def judgement(port_num):
    """
    用来判断端口号用的ip地址和sn号
    :param port_num: 传入的端口号
    :return: IP,SN 都是str型的
    """
    port_num = int(port_num)    # 先将传入的参数进行字符化处理
    if (30002 <= port_num <= 30200) or (30402 <= port_num <= 30500)\
            or (30501 <= port_num <= 30600) or (30801 <= port_num <= 31200):
        ip = '10.65.26.143'
        sn = 'de221685-5460-4c50-80ff-3d322eb5b019'
    elif (30201 <= port_num <= 30400) or (30601 <= port_num <= 30700)\
            or (31201 <= port_num <= 32000):
        ip = '10.65.26.144'
        sn = '90829856-5781-41fe-a6d4-d1ec5f16e548'
    elif 32001 <= port_num <= 32400:
        ip = '192.168.9.74'
        sn = '2462f05b-c90a-4a92-9469-43444d0297dd'
    elif 32401 <= port_num <= 32800:
        ip = '192.168.9.83'
        sn = 'a742eaa1-7348-472b-b32d-a9f00abdbda0'
    elif 32801 <= port_num <= 33200:
        ip = '192.168.9.86'
        sn = 'da5526ba-afc0-4eae-a7a5-fcd947126c5f'
    elif 33201 <= port_num <= 33600:
        ip = '192.168.9.88'
        sn = '584a2b58-8878-4c37-9144-cd4f427c7d04'
    elif 33601 <= port_num <= 34000:
        ip = '192.168.9.89'
        sn = '5cf81848-1122-4d0c-b665-2b44f1899a13'
    elif 34001 <= port_num <= 34400:
        ip = '192.168.9.94'
        sn = 'd3af993f-3f82-45ae-85e9-d8a093db4aff'
    elif 34401 <= port_num <= 34800:
        ip = '192.168.9.95'
        sn = 'da52699e-311f-4317-a675-12d07d59151d'
    elif 34801 <= port_num <= 35200:
        ip = '192.168.9.98'
        sn = '6e562d4f-9cfd-49b4-8c30-58b5d673b97d'
    elif 35201 <= port_num <= 35600:
        ip = '192.168.9.131'
        sn = '5cc7755c-a417-4cc7-9571-172753739f0d'
    elif 35601 <= port_num <= 36000:
        ip = '192.168.9.132'
        sn = 'b2c4ce75-4d77-445f-858d-650d24b53d44'
    elif 36001 <= port_num <= 36400:
        ip = '192.168.9.133'
        sn = '53d7c2e1-066b-4a63-aff9-48234d8d423b'
    elif 36401 <= port_num <= 36800:
        ip = '192.168.9.134'
        sn = 'c349eb79-e992-4a86-bb9b-f0983b13be7f'
    elif 36801 <= port_num <= 37200:
        ip = '192.168.9.135'
        sn = 'cc7d1a27-f180-477d-a361-f8d21988633e'
    elif 37201 <= port_num <= 37600:
        ip = '192.168.9.136'
        sn = 'db88f85c-d1cf-4a20-8521-3f62e4bcc335'
    elif 37601 <= port_num <= 38000:
        ip = '192.168.9.137'
        sn = '26eb74ff-dbf1-4bcc-ab21-b9f97af7c76a'
    elif 38001 <= port_num <= 38400:
        ip = '192.168.9.138'
        sn = '36c3de54-8547-41f1-8050-357fd9e6c972'
    elif 38401 <= port_num <= 38800:
        ip = '192.168.9.139'
        sn = '5ae573b7-5919-4337-a893-c7e0ab02b3c1'
    elif 38801 <= port_num <= 39200:
        ip = '192.168.9.140'
        sn = '3727f1f3-98a3-4e6e-b26e-c32936bcd7b2'
    elif 39201 <= port_num <= 39600:
        ip = '192.168.9.141'
        sn = '903dda4d-f78a-4780-97e3-00a0ac22dfdb'
    else:
        return False
    return ip, sn


def which_link(port_num, port_list, start_num=0):
    """
    判断该用哪个连接名字来进行下一步的操作
    :param port_num: 传入的端口号，用来查重
    :param port_list: 最开始应该为一个空列表，随着端口号的输入，而变得不空
    :param start_num: 起始后缀，默认为0；如果已有连接则需先去获得有多少连接数，再将此数传入进来
    :return: str
    """
    if port_num not in port_list:
        port_list.append(port_num)
        X = len(port_list) + start_num
    else:
        X = len(port_list) + start_num
    return "104转发%d" % X


if __name__ == '__main__':
    extract_data_into_a_json()
