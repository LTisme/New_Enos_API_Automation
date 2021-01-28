"""
#-*- coding: utf-8 -*-

Created on 2021/1/14 15:56

@author: LT
"""
import requests
import json


class ContentTypeDisposition(object):
    """用来自动识别请求头中的content-type类型，并处理所带的请求体数据，以让最后request有个最简洁的传参方式"""
    def __init__(self, data_=None, headers_=None):
        """
        将输入的请求头与请求体作为属性
        :param data_: 请求体，默认为None
        :param headers_: 请求头，默认为None
        """
        self.boundary = '----WebKitFormBoundary3wf0kPKxFBnmf0gQ'     # Boundary是得有，但又不需要那么严谨的东西，有这个格式就行
        self.data = data_
        self.headers = headers_
        self.URL = {
            'StationConfig': {
                # 获取每个场站的projid
                'childdetail': 'https://portal-lywz1.eniot.io/configuration/rest/site/childdetail',
                # 往场站信息里添加设备的url
                'adddevice': 'https://portal-lywz1.eniot.io/configuration/rest/site/adddevice',
                # 添加完设备后获得每个设备的objectID，以备后续Edge接入以及拓扑结构模板用到
                'childdetailpagestep': 'https://portal-lywz1.eniot.io/configuration/rest/site/childdetailpagestep',
                # 根据对应的objectID删除场站信息下的设备
                'deletedevice': 'https://portal-lywz1.eniot.io/configuration/rest/site/deletedevice'
            },
            'EdgeAccess': {
                # 获得一下所有盒子信息，防止同SN号盒子冲突
                'getallboxinfo': 'https://portal-lywz1.eniot.io/configuration/rest/access/getallboxinfo',
                # 添加盒子
                'addbox': 'https://portal-lywz1.eniot.io/configuration/rest/access/addbox',
                # 添加连接
                'addcollect': 'https://portal-lywz1.eniot.io/configuration/rest/access/addcollect',
                # 在对应盒子的对应连接下添加设备
                'adddevices': 'https://portal-lywz1.eniot.io/configuration/rest/access/adddevices',
                # 获得最新的设备模板
                'getalldevicetypes': 'https://portal-lywz1.eniot.io/configuration/rest/access/getalldevicetypes',
                # 发布
                'publishbox': 'https://portal-lywz1.eniot.io/configuration/rest/access/publishbox',
            }
        }

    def __post(self, url):
        """
        每个post方法都要用到的私有方法
        :param url: 对应方法的api
        :return: requests.models.Response 即返回response请求
        """
        if not isinstance(self.data, dict) and self.data is not None:     # 判断data是否是字典格式
            raise Exception("参数错误，data参数应为dict类型，或者为NoneType类型")
        elif self.data is None:   # 不带请求体来post执行
            res = requests.request("POST", url, headers=self.headers, )
        else:   # 正常执行字典格式的data请求体
            res = requests.request("POST", url, data=self.__dispatcher(), headers=self.headers, )
        return res

    def __content_type_multipart_form_data(self):
        """
        用来处理请求头的Content-Type为multipart/form-data格式的请求
        """
        # boundary格式不是那么严谨
        boundary = self.boundary

        # 开始拼接格式
        all_str = ''
        join_str = '--{}\r\nContent-Disposition: form-data; name="{}"\r\n\r\n{}\r\n'     # 每当data中有一个键值对，就需要用这个一次
        end_str = f'--{boundary}--'      # 结尾格式还需要在末尾加两个--符号

        # 开始获取data中的参数
        for key, value in self.data.items():
            all_str += join_str.format(boundary, key, value)
        final_str = all_str + end_str
        final_str = final_str.replace("\'", "\"")   # 必不能缺失
        # print(final_str)    # 可在正式用的时候注释掉，出问题的时候打开

        return final_str

    def __dispatcher(self):
        """
        调度员——用来识别格式，然后发给对应处理的私有方法
        """
        if "content-type" in self.headers:
            fd_val = str(self.headers["content-type"])
            if "boundary" in fd_val:
                # 返回真正的data
                data = self.__content_type_multipart_form_data().encode('utf-8')    # encode只能用在string上
            elif "json" in fd_val:
                # json的重点是分析哪些是要传的参数罢了
                data = json.dumps(self.data)    # json格式的需要用这种形式处理一下，需要dump成string
            else:
                raise Exception("multipart/form-data头信息错误，请检查content-type key是否包含boundary")
        else:
            raise Exception("请求头信息错误，不含content-type键，请检查")

        return data     # 返回请求体

    def request_method_stationdetail_childdetail(self):
        """
        场站信息中获取设备信息用的请求
        """
        url = self.URL['StationConfig']['childdetail']
        return self.__post(url)

    def request_method_stationdetail_adddevice(self):
        """
        场站信息中添加设备信息用的请求
        """
        url = self.URL['StationConfig']['adddevice']
        return self.__post(url)

    def request_method_stationdetail_deletedevice(self):
        """
        场站信息中删除设备用的请求
        """
        url = self.URL['StationConfig']['deletedevice']
        return self.__post(url)

    def request_method_stationdetail_childdetailpagestep(self):
        """
        场站信息中每添加一个设备后获取对应objectID信息用的请求
        """
        url = self.URL['StationConfig']['childdetailpagestep']
        return self.__post(url)

    def request_method_edge_getallboxinfo(self):
        """
        Edge接入中获取当前页面下所有盒子的信息
        """
        url = self.URL['EdgeAccess']['getallboxinfo']
        return self.__post(url)

    def request_method_edge_addbox(self):
        """
        Edge接入中新建一个盒子
        """
        url = self.URL['EdgeAccess']['addbox']
        return self.__post(url)

    def request_method_edge_addcollect(self):
        """
        Edge接入中在盒子下新建个连接
        """
        url = self.URL['EdgeAccess']['addcollect']
        return self.__post(url)

    def request_method_edge_adddevices(self):
        """
        Edge接入中在对应的盒子下的对应连接里添加设备
        """
        url = self.URL['EdgeAccess']['adddevices']
        return self.__post(url)

    def request_method_edge_getalldevicetypes(self):
        """获得最新的设备模板的对应ID"""
        url = self.URL['EdgeAccess']['getalldevicetypes']
        return self.__post(url)

    def request_method_edge_publishbox(self):
        """
        Edge接入中点击发布
        """
        url = self.URL['EdgeAccess']['publishbox']
        return self.__post(url)


class Headers(object):
    def __init__(self):
        self.headers_multipart = {
            # boundary与主类的self.boundary要一样
            'content-type': 'multipart/form-data; boundary=----WebKitFormBoundary3wf0kPKxFBnmf0gQ'
        }

        self.headers_json = {
            'content-type': 'application/json'
        }

        self.headers_query_templates = {
            # 这是shujun.wu这个账号对应的各个参数，无须修改；若是TSKJ的名字，则需要换成其对应的各个参数
            # 请求设备模板，无需content-type，因为不发请求体，url会自动识别的
            'eos_auth': json.dumps({"uid": "35e35736-ce9a-4d1b-b2d5-14ea8c279353", "token": "IAM_s16107615692591",
                                    "orgCode": "1859febe5ce70000", "userName": "shujun.wu", "locale": "zh-CN"})
        }


class Data(object):
    """
    各个api用的data-Body字典格式
    """

    @staticmethod
    def station_childdetail(siteid):    # 这个用到次数为1次
        data = {
            'parentid': siteid,
            'grouptype': 'true',
        }
        return data

    @staticmethod
    def station_childdetailpagestep(projid):    # 这个需要用到设备数+1次
        data = {
            'pagesize': 10,
            'type': 0,
            'pivot': 'null',
            'attr': {'parentid': projid, 'name': ''}  # 这个parentID是projid！！！！！！
        }
        return data

    @staticmethod
    def station_adddevice(projid, catid, device_name, maxCurrent, TransformerCapacity, siteID, Un="400"):  # 这个需要用到设备数次
        """
        :param projid: 前面post已获得
        :param catid: 前面post已获得
        :param device_name: 数据结构中已获得
        :param maxCurrent: 数据结构中已获得
        :param TransformerCapacity: 数据结构中已获得
        :param siteID: 数据结构中已获得
        :param Un: 额定线电压，一般都填400
        :return: Body结构,dict
        """
        data = {    # data里的设备名、Un、maxCurrent、TransformerCapacity、siteID等都是需要从Excel里读取的
            "projid": projid,
            "catid": catid,
            "attr": {"name.default": device_name, "name.zh-CN": device_name, "Un": Un, "maxCurrent": maxCurrent,
                     "TransformerCapacity": TransformerCapacity, "model": "-1", "typeId": "227", "typeName": "多功能电表",
                     "innerVer": "-1", "inputer": "shujun.wu", "isAttachedSite": "false", "siteID": siteID}
        }       # 创建一个设备信息字典
        return data

    @staticmethod
    def station_deletedevice(objectID):  # 这个是根据每个设备的特定
        data = {
            'id': objectID,
        }
        return data

    @staticmethod
    def edge_getallboxinfo(siteid):  # 获得edge中盒子信息
        data = {
            'siteid': siteid,   # 这个i必须小写
            'type': 0,
        }
        return data

    @staticmethod
    def edge_addbox(siteId, boxName, boxSN):  # 添加盒子
        """
        edge接入中新建一个盒子
        :param siteId: 外界传入站点的siteID
        :param boxName: 盒子名字，一般采取IP加盒子，如192.168.9.133盒子
        :param boxSN: 端口号对应的SN号
        :return: dict
        """
        data = {
            "siteId": siteId,   # 鬼鬼，这个键的I必须大写
            "boxName": boxName,
            "boxSN": boxSN,
            "deviceList": []    # 新建盒子时候默认设备列表为空
        }
        return data

    @staticmethod
    def edge_addcollect(siteId, collectname, ip, portnum):  # 添加连接，与盒子无关，与siteID有关
        """
        edge接入中添加一个连接
        :param siteId: 场站的siteID
        :param collectname: 连接名字
        :param ip: 连接用到的ip
        :param portnum: 连接用到的portnum
        :return:
        """
        data = {
            "siteid": siteId,  # 这个键的i必须小写
            "collect": {
                "attributes": {
                    "name": collectname, "connIP": f"{ip}:{portnum}", "connType": "TCP_SVR",
                    "KEEP_ALIVE": "true"}, "collectType": "0"},     # 之前KEEP_ALIVE处用的布尔True，被证明是错误的
            "devicetemplates": []   # 新建连接时，设备模板列表默认为空
        }
        return data

    @staticmethod
    def edge_adddevices(siteId, boxId, objectID, collectId, modbus, manufacturer, deviceId):  # 在已有的连接中勾选之前在场站信息中添加过的设备
        modbus = int(modbus)
        if '水电' in manufacturer and modbus != 1:
            AI = "%d-%d" % (91 * (modbus - 1), 91 * modbus - 1)
            DI = "%d-%d" % (modbus, modbus)
        elif modbus != 1:
            AI = '%d-%d' % (78 * (modbus - 1), 78 * modbus - 1)
            DI = '%d-%d' % (4 * modbus - 3, 4 * modbus)
        else:
            AI = "-1"
            DI = "-1"
        data = {"siteId": siteId, "boxId": boxId,
                "attachList": [objectID],
                "deviceConfList": [{"attributes": {
                    "logicalID": modbus, "realPointOffset": 3, "realPointOffset_0": AI, "realPointOffset_1": DI,
                    "realPointOffset_2": "-1"}, "deviceId": deviceId, "cimUuid": objectID,
                    "collectId": collectId}], "detachList": []}
        return data

    @staticmethod
    def edge_publishbox(siteid, boxid):  # 点击发布就好了哦
        data = {
            "siteid": siteid,
            "boxid": boxid,
        }

        return data
