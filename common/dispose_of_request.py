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
from multiprocessing import Pool, Manager, cpu_count     # 进程池用
import time     # 计时用


logging.basicConfig(filename='api_logging.log', level=logging.DEBUG,
                    format='%(asctime)s - [line:%(lineno)d] - %(levelname)s - %(message)s')
logging.info('Start of Program')

os.chdir(os.path.dirname(os.path.realpath(__file__)))
api_functions.extract_data_into_a_json()    # 读取data.xlsx里的数据，并生成data.json格式的文件
with open('data.json', encoding='UTF-8') as fbj:
    origin_data = json.load(fbj)      # 现在data就是想要的数据结构


headers = Headers()
body = Data()   # 这个实例里包含每个特定api操作的要求格式

# 先post请求getalldevicestype以获得内容，再用厂家名、CT、PT正则匹配得出结果
templates = api_relogic.get_all_devices_type(headers, logging)


def worker(queue, index):
    process_id = "Process-" + str(index)
    print(process_id + " start!\n")
    while not queue.empty():    # 任务队列只要不为空就会一直循环
        each_station = queue.get(timeout=2)     # 从队列中取得任务
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

        # 逻辑开始
        if len(st.json()['data']) == 0:
            print('该场站下没有盒子')
            # 往场站信息里添加盒子
            new_list = api_relogic.add_devices_in_station_info(siteID, each_station, body, headers, logging)    # 添加完成并返回了一个含多属性的列表

            # 去到Edge接入中新建盒子
            box_set = set([(elem['ip'], elem['sn']) for elem in new_list])  # 现在box_set是个集合类型
            api_relogic.add_boxes_in_egde_access(siteID, body, headers, box_set, logging)   # 已新建完盒子

            # 添加完盒子后需要开始添加所有连接，若有残留连接在也不需要端口号筛重
            st = exp.request_method_edge_getallboxinfo()  # 再次获得Edge中的盒子信息，这样是因为可以在不删除连接的情况下删除盒子
            if len(st.json()['data'][0]['collectList']) != 0:   # 说明此站有残留连接，需要在日志里指出，让人去检查
                print(f'siteid:{siteID}的站点有残留连接，请检查！')
                logging.warning(f'siteid:{siteID}的站点有残留连接，请检查！')
                api_relogic.add_collects_in_edge_access(siteID, body, headers, new_list, logging)   # 残留连接不影响连接名后缀
            else:   # 说明无残留连接，是理想的情况
                api_relogic.add_collects_in_edge_access(siteID, body, headers, new_list, logging)

            # 连接添加完后开始选中已添加的设备
            api_relogic.select_devices_to_corresponding_collect_in_edge_access(siteID, body, headers, new_list, templates, logging)

            # 发布盒子
            api_relogic.publish_sn_in_edge_access(siteID, body, headers, box_set, logging)  # 发布盒子

            # 发布完后就是要去做拓扑结构的导入了
            SYNCHRONIZE_DICT['devices_list'] = new_list     # 首先把对应的设备字典填入同步字典
            api_relogic.synchronize_corresponding_station_with_template(siteID, SYNCHRONIZE_DICT, logging)  # 发布

        else:
            print('该场站下有盒子')
            # TODO: 首先getallboxinfo，因为有盒子了嘛，然后去找其下的端口号——注意端口号只于连接有关，与盒子无关，故是去判断连接！！！
            if len(st.json()['data'][0]['collectList']) == 0:    # 说明盒子下无连接，则可以直接往场站信息中添加设备，然后后续操作
                # 往场站信息里添加盒子，添加完成后返回了设备的信息
                new_list = api_relogic.add_devices_in_station_info(siteID, each_station, body, headers, logging)    # 添加完成并返回了一个含多属性的列表

                # 场站信息里添加完设备之后，就开始在Edge接入添加盒子
                already_exists_sn_list = [each_sn['boxSN'] for each_sn in st.json()['data']]  # 获得已有的盒子sn号列表
                box_set = set([(elem['ip'], elem['sn']) for elem in new_list])  # 现在box_set是个集合类型
                api_relogic.add_boxes_in_egde_access(
                    siteID, body, headers, box_set, logging, already_exists_sn_list=already_exists_sn_list)

                # 盒子添加完后就是连接的建立，不需要再判断是否有残留连接了，即连接名从104转发1开始
                api_relogic.add_collects_in_edge_access(siteID, body, headers, new_list, logging)   # 添加连接

                # 连接添加完后开始选中已添加的设备
                api_relogic.select_devices_to_corresponding_collect_in_edge_access(siteID, body, headers, new_list,
                                                                                   templates, logging)

                # 发布盒子
                api_relogic.publish_sn_in_edge_access(siteID, body, headers, box_set, logging)  # 发布盒子

                # 发布完后就是要去做拓扑结构的导入了
                SYNCHRONIZE_DICT['devices_list'] = new_list  # 首先把对应的设备字典填入同步字典
                api_relogic.synchronize_corresponding_station_with_template(siteID, SYNCHRONIZE_DICT, logging)  # 发布

            else:   # 说明有盒子有连接，则去遍历连接，查看有无对应的端口号——连接名需要获得已有连接数量来变化
                # 获得连接下的所有端口号的列表，函数会判断是否跳过已重复的端口号的设备
                collect_portnum_list = [each_collect['attributes']['connIP'][-5:] for each_collect in st.json()['data'][0]['collectList']]
                new_list = api_relogic.add_devices_in_station_info(
                    siteID, each_station, body, headers, logging, collect_portnum_list=collect_portnum_list)    # 添加完成并返回了一个含多属性的列表
                if not new_list:    # new_list为空，则说明场站已有全部的端口号了，不需要再做了
                    print(f'siteid:{siteID}场站已有全部的端口号了！')
                    logging.warning(f'siteid:{siteID}场站已有全部的端口号了！')
                    continue    # 跳到下个站点执行

                # TODO: 2.1遍历查看Edge接入中无对应的SN号盒子
                already_exists_sn_list = [each_sn['boxSN'] for each_sn in st.json()['data']]    # 获得已有的盒子sn号列表
                box_set = set([(elem['ip'], elem['sn']) for elem in new_list])  # 现在box_set是个集合类型
                # 将获得的已有的盒子sn号列表传入添加盒子函数做查重判断
                api_relogic.add_boxes_in_egde_access(
                    siteID, body, headers, box_set, logging, already_exists_sn_list=already_exists_sn_list)

                # 盒子添加完后就是连接的建立，需要再判断是否有残留连接，连接名从104转发（已有连接数）+1开始
                api_relogic.add_collects_in_edge_access(
                    siteID, body, headers, new_list, logging, startnum=len(st.json()['data'][0]['collectList']))  # 添加连接

                # 连接添加完后开始选中已添加的设备
                api_relogic.select_devices_to_corresponding_collect_in_edge_access(siteID, body, headers, new_list,
                                                                                   templates, logging)

                # 发布盒子
                api_relogic.publish_sn_in_edge_access(siteID, body, headers, box_set, logging)  # 发布盒子

                # 发布完后就是要去做拓扑结构的导入了
                SYNCHRONIZE_DICT['devices_list'] = new_list  # 首先把对应的设备字典填入同步字典
                api_relogic.synchronize_corresponding_station_with_template(siteID, SYNCHRONIZE_DICT, logging)  # 发布


if __name__ == '__main__':
    start_time = time.time()  # 开始时间

    # 填充任务队列
    manager = Manager()
    work_queue = manager.Queue(len(origin_data))    # 有多少个站点就有多少个任务
    for each_station in origin_data:    # 填充任务队列
        work_queue.put(each_station)

    # 创建非阻塞进程
    max_ = 2 * cpu_count()  # 当前电脑核数×2 个进程数
    pool = Pool(processes=max_)     # 提供指定数目的进程，当有新任务请求时，若进程池没满则需要
    for i in range(max_):
        pool.apply_async(func=worker, args=(work_queue, i))     # 创建非阻塞进程

    print("Start processing...")
    pool.close()    # 关闭进程池，关闭后pool不再接收新的请求
    pool.join()     # 等待pool中所有子进程执行完成，必须放在close语句之后

    end_time = time.time()  # 结束时间
    print("All consumed time is ", end_time - start_time, " seconds.")
logging.info('End of Program')
