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


if __name__ == '__main__':
    extract_data_into_a_json()
