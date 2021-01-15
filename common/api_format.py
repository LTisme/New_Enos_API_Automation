"""
#-*- coding: utf-8 -*-

Created on 2021/1/14 15:56

@author: LT
"""
import requests


class ContentTypeDisposition(object):
    """用来自动识别请求头中的content-type类型，并处理所带的请求体数据，以让最后request有个最简洁的传参方式"""
    def __init__(self, data_, headers_):
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
                # 发布
                'publishbox': 'https://portal-lywz1.eniot.io/configuration/rest/access/publishbox',
            }
        }

    def __post(self, url):
        """
        每个post方法都要用到的私有方法
        :param url: 对应方法的api
        :return: requests.models.Response
        """
        if not isinstance(self.data, dict):     # 判断data是否是字典格式
            raise Exception("multipart/form-data参数错误，data参数应为dict类型")
        else:   # 正常执行
            res = requests.request("POST", url, data=self.__dispatcher().encode('utf-8'), headers=self.headers, )
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
        final_str = final_str.replace("\'", "\"")
        print(final_str)

        return final_str

    def __dispatcher(self):
        """
        调度员——用来识别格式，然后发给各个私有方法对应处理的方法
        """
        if "content-type" in self.headers:
            fd_val = str(self.headers["content-type"])
            if "boundary" in fd_val:
                # 返回真正的data
                data = self.__content_type_multipart_form_data()
            elif "json" in fd_val:
                # json格式的请求体只用把json内容，也就是data直接放进去就好了啊，json的重点是分析哪些是要传的参数罢了
                data = self.data
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
        场站信息中添加设备信息用的请求
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
            'siteid': siteid,
            'type': 0,
        }
        return data
