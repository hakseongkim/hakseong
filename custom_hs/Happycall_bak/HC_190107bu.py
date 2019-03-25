#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

reload(sys)
sys.setdefaultencoding('utf-8')
from concurrent import futures
import argparse
import grpc
import os
import random
from google.protobuf import empty_pb2
from google.protobuf import struct_pb2 as struct
import time
import syslog
import pymysql
import datetime
import re

exe_path = os.path.realpath(sys.argv[0])
bin_path = os.path.dirname(exe_path)
lib_path = os.path.realpath(bin_path + '/../lib/python')
sys.path.append(lib_path)

from maum.m2u.facade import userattr_pb2
from maum.m2u.da import provider_pb2
from maum.m2u.da.v3 import talk_pb2_grpc
from maum.m2u.da.v3 import talk_pb2
from maum.m2u.facade import front_pb2

# Custom import
#from qa.util import *
from qa import basicQA
from custom_hs.sds import SDS
from qa.util import Util

# echo_simple_classifier = {
#    "echo_test": {
#        "regex": [
#            "."
#        ]
#    }

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
Session_Value = []
_NOTHING_FOUND_INTENT_ = "의도를 찾지 못했습니다."
model = 'Happy_Call_HH'

#def setSessionValue(session_id, key, value):
#    try:
#        sessionList = [x.get("session_id") for x in Session_Value]
#        findIndex = sessionList.index(session_id)
#        Session_Value[findIndex][key] = value
#    except Exception as err:
#        pass
#
#def getSessionValue(session_id, key):
#    keyValue = None
#    isNew = False
#
#    if len(Session_Value) > 0:
#        sessionList = [x.get("session_id") for x in Session_Value]
#        try:
#            findIndex = sessionList.index(session_id)
#            keyValue = Session_Value[findIndex][key]
#        except Exception as err:
#            isNew = True
#    else:
#        isNew = True
#
#    if isNew:
#        Session_Value.append({"session_id" : session_id, "model" : ""})
#        keyValue = Session_Value[len(Session_Value)-1][key]
#
#    return keyValue
#
#def RegEx(self, session_id):
#    print("RegEx call!!")
#
#    print("get model : " + str(getSessionValue(session_id, "model")))
#    modelname = str(getSessionValue(session_id, "model"))
#    if modelname == "":
#        intent = "Happy_Call_HH"
#        setSessionValue(session_id, "model", intent)
#    elif modelname == "2":
#        intent = "privacy"
#        setSessionValue(session_id, "model", intent)
#
#    #intent = str(getSessionValue(session_id, "model"))
#    return intent

class EchoDa(talk_pb2_grpc.DialogAgentProviderServicer):
    # STATE
    # state = provider_pb2.DIAG_STATE_IDLE
    init_param = provider_pb2.InitParameter()

    # PROVIDER
    provider = provider_pb2.DialogAgentProviderParam()
    provider.name = 'control'
    provider.description = 'control intention return DA'
    provider.version = '0.1'
    provider.single_turn = True
    provider.agent_kind = provider_pb2.AGENT_SDS
    provider.require_user_privacy = True

    # PARAMETER

    def __init__(self):
        syslog.syslog('init')
        self.state = provider_pb2.DIAG_STATE_IDLE
        syslog.syslog(str(self.state))
        self.qa_util = Util()
        self.Sds = SDS()

    #
    # INIT or TERM METHODS
    #

    def IsReady(self, empty, context):
        print 'V3 ', 'IsReady', 'called'
        status = provider_pb2.DialogAgentStatus()
        status.state = self.state
        return status

    def Init(self, init_param, context):
        print 'V3 ', 'Init', 'called'
        self.state = provider_pb2.DIAG_STATE_INITIALIZING
        # COPY ALL
        self.init_param.CopyFrom(init_param)
        # DIRECT METHOD
        self.state = provider_pb2.DIAG_STATE_RUNNING
        # returns provider
        result = provider_pb2.DialogAgentProviderParam()
        result.CopyFrom(self.provider)
        print 'result called'
        return result

    def Terminate(self, empty, context):
        print 'V3 ', 'Terminate', 'called'
        # DO NOTHING
        self.state = provider_pb2.DIAG_STATE_TERMINATED
        return empty_pb2.Empty()

    def GetUserAttributes(self, empty, context):
        print 'V3 ', 'GetUserAttributes', 'called'
        result = userattr_pb2.UserAttributeList()
        attrs = []

        # UserAttribute의 name은 DialogAgentProviderParam의 user_privacy_attributes에
        # 정의한 이름과 일치해야 한다.
        # 이 속성은 사용자의 기본 DB 외에 정의된 속성 외에 추가적으로 필요한
        # 속성을 정의하는 것입니다.

        lang = userattr_pb2.UserAttribute()
        lang.name = 'lang'
        lang.title = '기본 언어 설정'
        lang.type = userattr_pb2.DATA_TYPE_STRING
        lang.desc = '기본으로 사용할 언어를 지정해주세요.'
        attrs.append(lang)

        loc = userattr_pb2.UserAttribute()
        loc.name = 'location'
        loc.title = '기본 지역'
        loc.type = userattr_pb2.DATA_TYPE_STRING
        loc.desc = '기본으로 조회할 지역을 지정해주세요.'
        attrs.append(loc)

        device = userattr_pb2.UserAttribute()
        device.name = 'device'
        device.title = '기본 디바이스'
        device.type = userattr_pb2.DATA_TYPE_STRING
        device.desc = '기본으로 사용할 디바이스를 지정해주세요.'
        attrs.append(device)

        country = userattr_pb2.UserAttribute()
        country.name = 'time'
        country.title = '기준 국가 설정'
        country.type = userattr_pb2.DATA_TYPE_STRING
        country.desc = '기본으로 조회할 국가를 지정해주세요.'
        attrs.append(country)

        result.attrs.extend(attrs)
        return result

    #
    # PROPERTY METHODS
    #

    def GetProviderParameter(self, empty, context):
        print 'V3 ', 'GetProviderParameter', 'called'
        result = provider_pb2.DialogAgentProviderParam()
        result.CopyFrom(self.provider)
        return result

    def GetRuntimeParameters(self, empty, context):
        print 'V3 ', 'GetRuntimeParameters', 'called'
        result = provider_pb2.RuntimeParameterList()
        params = []

        db_host = provider_pb2.RuntimeParameter()
        db_host.name = 'db_host'
        db_host.type = userattr_pb2.DATA_TYPE_STRING
        db_host.desc = 'Database Host'
        db_host.default_value = '171.64.122.134'
        db_host.required = True
        params.append(db_host)

        db_port = provider_pb2.RuntimeParameter()
        db_port.name = 'db_port'
        db_port.type = userattr_pb2.DATA_TYPE_INT
        db_port.desc = 'Database Port'
        db_port.default_value = '7701'
        db_port.required = True
        params.append(db_port)

        db_user = provider_pb2.RuntimeParameter()
        db_user.name = 'db_user'
        db_user.type = userattr_pb2.DATA_TYPE_STRING
        db_user.desc = 'Database User'
        db_user.default_value = 'minds'
        db_user.required = True
        params.append(db_user)

        db_pwd = provider_pb2.RuntimeParameter()
        db_pwd.name = 'db_pwd'
        db_pwd.type = userattr_pb2.DATA_TYPE_AUTH
        db_pwd.desc = 'Database Password'
        db_pwd.default_value = 'minds67~'
        db_pwd.required = True
        params.append(db_pwd)

        db_database = provider_pb2.RuntimeParameter()
        db_database.name = 'db_database'
        db_database.type = userattr_pb2.DATA_TYPE_STRING
        db_database.desc = 'Database Database name'
        db_database.default_value = 'ascar'
        db_database.required = True
        params.append(db_database)

        result.params.extend(params)
        return result
    def OpenSession(self, request, context):
        print "openSession"

        #param = {}
        #bizRes = {}
        lectureInfo = {}
        resMessage = 'success'
        meta = ''
        lectureNum = ''
        session_id = request.session.id
        #self.showKeyValue(context.invocation_metadata())

        if 'meta' in request.utter.meta:
             #meta = eval(request.utter.meta['meta'].replace('null','\"\"'))
             meta = request.utter.meta['meta']

             if 'intent' in meta:
                slots = meta['intent']['slots']
                if 'lectureNumber' in slots:
                    lectureNum = slots['lectureNumber']['value']

        #requestParam = Common.setMetaToParamMap(lectureNum=lectureNum,userTalk=' ' ,request=request, isopenRequest=True,session_id=session_id)
        localSessionObj = session_id
        print 'OpenSession id: '+str(request.session.id)

        result = talk_pb2.TalkResponse()
        res_meta = struct.Struct()
        #res_meta['response'] = bizRes
        result.response.meta.CopyFrom(res_meta)

        #session 정보 ,session data 10k
        result.response.session_update.id = session_id
        res_context = struct.Struct()
        res_context['session_data'] = str(lectureInfo)
        result.response.session_update.context.CopyFrom(res_context)

        print 'OpenSession_'
        return result

    def OpenSkill(self, request, context):
        print "OpenSkill start"
        print 'Open request: '+str(request)
        session_id = request.session.id
        print 'open_session_data: '+ str(session_id)+', '+str(context)
        result = talk_pb2.TalkResponse()
        print 'OpenSkill end'
        return result


    def CloseSkill(self, request, context):

        result = talk_pb2.CloseSkillResponse()
        return result

    def EventT(self, empty, context):
        print 'V3 ', 'DA Version 3 EventT', 'called'

        # DO NOTHING
        return empty_pb2.Empty()


    def DBConnect(self, query):
        conn = pymysql.connect(user="aicc",
                               password="ggoggoma",
                               host="aicc-bqa.cjw9kegbaf8s.ap-northeast-2.rds.amazonaws.com",
                               database="happycall",
                               charset="utf8",
                               use_unicode=False)
        curs = conn.cursor(pymysql.cursors.DictCursor)
        #query = "select * from test;"
        print(query)
        curs.execute(query)
        print("query good!")
        rows = curs.fetchall()

        print(rows)
        curs.execute("commit;")
        curs.close()
        conn.close()
        return rows
    def DBConnect_HC(self, query):
        conn = pymysql.connect(user="maum",
                               password="ggoggoma",
                               host="localhost",
                               database="HappyCall",
                               charset="utf8",
                               use_unicode=False)
        curs = conn.cursor(pymysql.cursors.DictCursor)
        #query = "select * from test;"
        print(query)
        curs.execute(query)
        print("query good!")
        rows = curs.fetchall()

        print(rows)
        curs.execute("commit;")
        curs.close()
        conn.close()
        return rows


    def Talk(self, talk, context):
        #print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        #print(talk)
        #print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        a = {}
        """
        talk.utter.utter : 사용자 발화
        talk_res를 return

        talk_res.response.speech.utter : 챗봇 발화
        """
        talk.utter.utter = talk.utter.utter + ";$callSeq=6$call_Id=333"
        print("talk : ", talk.utter.utter)
        seq = talk.utter.utter[talk.utter.utter.index(";$callSeq")+10:talk.utter.utter.index(";$callSeq")+11]
        call_id = talk.utter.utter[talk.utter.utter.index("$call_Id")+9:talk.utter.utter.index("$call_Id")+12]
        print("", str(seq) + "," + str(call_id))
        phoneNum = self.DBConnect("select cust_tel_no from campaign_target_list_tb where contract_no = '" + seq + "';")
        phoneNum = phoneNum[0]['cust_tel_no']
        #phoneNum = '01084520997'
        uttertext = talk.utter.utter[talk.utter.utter.find(";$callSeq"):]
        #uttertext = talk.utter.utter[talk.utter.utter.find("$callSeq"):]
        talk.utter.utter = talk.utter.utter.replace(uttertext,"")

        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print("talk : ", talk.utter.utter)
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
       
        # SDS.dp.slots["product_code"] = "A"
        #session_id = talk.session.id
        dbsession = self.DBConnect("select session_value,cust_tel_no,cust_nm,join_time,talk_time,insured_contractor,insured_person,insured_closeproduct,address_main,address_sub,product_code,prod_name from campaign_target_list_tb where contract_no = '" + seq + "';")
        # cust_nm 통화자(가입자)
        # join_time 전체 시간 호출
        # join_month 가입 월
        # join_day 가입 일
        # insurance_contractor 가입 계약자
        # insurance_insured 가입 피보험자
        # insurance_closeproduct 무해지상품 가입여부
        # address_main 메인주소
        # address_sub 세부주소
        
        phone = dbsession[0]['cust_tel_no']
        user_name = dbsession[0]['cust_nm']

        join_time = dbsession[0]['join_time']
        print ("join_time : " + str(join_time))
        join_strp = datetime.datetime.strptime(str(join_time), '%Y-%m-%d %H:%M:%S')
        join_month = join_strp.month
        join_day = join_strp.day

        talk_time = dbsession[0]['talk_time']
        talk_strp = datetime.datetime.strptime(str(talk_time), '%Y-%m-%d %H:%M:%S')
        talk_month = talk_strp.month
        talk_day = talk_strp.day
        talk_hour = talk_strp.hour
        talk_minute = talk_strp.minute

        insured_contractor = dbsession[0]['insured_contractor']
        insured_person = dbsession[0]['insured_person']
        insured_closeproduct = dbsession[0]['insured_closeproduct']
        privacy_add1 = dbsession[0]['address_main']
        privacy_add2 = dbsession[0]['address_sub']
        product_code = dbsession[0]['product_code']
        prod_name = dbsession[0]['prod_name']

        if dbsession[0]['session_value'] is None:
            dbsessioncode = talk.session.id
            self.DBConnect("update campaign_target_list_tb set session_value = '" + str(dbsessioncode) + "' where contract_no = '" + seq + "';")
            session_id = dbsessioncode
        else:
            session_id = int(dbsession[0]['session_value'])

        talk_res = talk_pb2.TalkResponse()

        ##초기 모델 설정
        dbsession = self.DBConnect("select model from campaign_target_list_tb where contract_no = '" + seq + "';")
        if dbsession[0]['model'] is None:
            model = "Happy_Call_HH"
        else:
            model = dbsession[0]['model']

        #question = talk.utter.utter
        meta = dict()
        #meta['seq_id'] = util.time_check(0)
        meta['log_type'] = 'SVC'
        meta['svc_name'] = 'DA'

        #output = ""
        original_answer = ""
        engine_path = list()
        answer_engine = "None"
        status_code = ""
        status_message = ""
        flag = False
        weight = 0
        code = 'None'
        sds_intent = ""



                

        # SDS
        dbtask = self.DBConnect("select task from campaign_target_list_tb where contract_no = '" + seq + "';")
        task = dbtask[0]['task']
        sds_intent = self.Sds.GetIntent(talk.utter.utter, model)
        if task == 'task2' and sds_intent == "affirm":
            print("성공11111")
            sds_res = self.Sds.Talk(talk.utter.utter, session_id, model, product_code)
            self.DBConnect("update campaign_target_list_tb set model='privacy' where contract_no = '" + seq + "';")
            model = 'privacy'

        #입력받는 주소를 여기다가 처리를 해줘야함
        if task == 'PRIVACY2' and sds_intent == "affirm":
            print("성공22222")
            print("g")
            talk.utter.utter = '$next$'
            self.DBConnect("update campaign_target_list_tb set model='Happy_Call_HH' where contract_no = '" + seq + "';")
            model = 'Happy_Call_HH'
        if task == 'PRIVACY3' and sds_intent == "privacy3":
            print("성공333333")
            self.DBConnect("update campaign_target_list_tb set model='Happy_Call_HH' where contract_no = '" + seq + "';")
            model = 'Happy_Call_HH'


        sds_res = self.Sds.Talk(talk.utter.utter, session_id, model, product_code)

        #self.DBConnect("update test set task='" + sds_res['current_task'] + "' where contract_no = '" + seq + "';")
        sds_intent = self.Sds.GetIntent(talk.utter.utter, model)
        print("sds_intent의 값 : " + str(sds_intent))

        # 결과값 DB에 저장하는 방식
        b = []
        b.append("time")
        b.append("timeAffirm")
        b.append("timeEnd")
        for i in range(1, 15):
            b.append("task" + str(i))
        for i in range(1, 4):
            b.append("PRIVACY" + str(i))


        if task in b:
            camp_id_db = self.DBConnect("select camp_id from hc_hh_campaign_info where task = '" + task  + "';")
            print (camp_id_db)
            camp_id = str(camp_id_db[0]['camp_id'])
            call_id_db = self.DBConnect("select camp_id from hc_hh_campaign_info where task = '" + task  + "';")
            print (camp_id_db)
            camp_id = str(camp_id_db[0]['camp_id'])
            if sds_intent == 'affirm':
                self.DBConnect("insert into hc_hh_campaign_score (call_id, contract_no, info_seq, info_task, task_value) values ('"+call_id+"','"+seq+"','"+camp_id+"','"+task +"','Y')");
            elif sds_intent == 'negate':
                #self.DBConnect("update campaign_target_list_tb set " + task + "='아니오' where contract_no = '" + seq + "';")
                self.DBConnect("insert into hc_hh_campaign_score (call_id, contract_no, info_seq, info_task, task_value) values ('"+call_id+"','"+seq+"','"+camp_id+"','"+task +"','N')");
            elif sds_intent == 'overlap' or sds_intent == 'noproportion':
                self.DBConnect("insert into hc_hh_campaign_score (call_id, contract_no, info_seq, info_task, task_value) values ('"+call_id+"','"+seq+"','"+camp_id+"','"+task +"','중복')")    ;
            elif sds_intent == 'nooverlap' or sds_intent == 'proportion':
                self.DBConnect("insert into hc_hh_campaign_score (call_id, contract_no, info_seq, info_task, task_value) values ('"+call_id+"','"+seq+"','"+camp_id+"','"+task +"','비례')")    ;
            else:
                self.DBConnect("insert into hc_hh_campaign_score (call_id, contract_no, info_seq, info_task, task_value) values ('"+call_id+"','"+seq+"','"+camp_id+"','"+task +"','입력')")    ;
            #    self.DBConnect("update hc_hh_campaign_score set " + task + "='"+talk.utter.utter+"' where contract_no = '" + seq + "';")

       #디비 이관 전 작업하던더
       #if task is not None or sds_intent != 'next':
           #self.DBConnect("insert into hc_hh_1_result (phone, user_name, session_name, model, task, utter, intent, request_time) values('" + str(phone) + "','" + user_name + "','" + str(session_id) + "','" + model + "','" + str(task) + "','" + talk.utter.utter + "','" + sds_intent + "',NOW());")

        #if sds_res['current_task'] == "timeEnd" and sds_res['intent'] == "affirm":
        #현재 위치를 저장하는 로직
        self.DBConnect("update campaign_target_list_tb set task='"+ sds_res['current_task'] + "' where contract_no = '" + seq + "';")

        print("SDS Start!")
        #dbtask = self.DBConnect("select task from test where contract_no = '" + seq + "';")
        #task = dbtask[0]['task']

        #print("++++++++++++++++taskname : " + sds_res['current_task'] + "intent : " + dialog_act)


        #그렇다면 넘어가는 로직을 여기다가 잡아놔야 할 것 같음
        # 값을 append에 포함되지 않을 경우, 해당로직을 건너 뛰는 것으로...

        # SDS
        dbtask = self.DBConnect("select task from campaign_target_list_tb where contract_no = '" + seq + "';")
        task = dbtask[0]['task']
        if task == 'task4' and insured_contractor == insured_person:
            talk.utter.utter = "$task4$"
            self.DBConnect("update campaign_target_list_tb set task='task5' where contract_no = '" + seq + "';")
            sds_res = self.Sds.Talk(talk.utter.utter, session_id, model, product_code)

        sds_list = []
#        tasknumber = task.find('task':)
        if product_code == 'b': 
            sds_list.append(9)
            sds_list.append(11)
            #sds_list.append(13)
#        if product_code == 'a': sds_list.append(9,10,11,12,13,14)
#        if product_code == 'a': sds_list.append(9,10,11,12,13,14)
        print (sds_list)
        task9_info = ""
        task11_info = ""
        task13_info = ""
        
        if sds_list == []:
            pass
        elif max(sds_list) == 9:
            task9_info = "다음부터 진행되는 질문은 담보문항에 대한 질문입니다."
        elif max(sds_list) == 11:
            task11_info = "다음부터 진행되는 질문은 담보문항에 대한 질문입니다."
        elif max(sds_list) == 13:
            task13_info = "다음부터 진행되는 질문은 담보문항에 대한 질문입니다."
        for sds_temp in sds_list:
            dbtask = self.DBConnect("select task from campaign_target_list_tb where contract_no = '" + seq + "';")
            task = dbtask[0]['task']
            if task is None or task == "":
                tasknumber = ""
            else:
                tasknumber = task[4:]
                print("tasknumber, sds_temp : "+tasknumber + str(sds_temp))
                if tasknumber == str(sds_temp):
                    talk.utter.utter = "$task"+ str(sds_temp) +"$"
                    print("utter가 들어간 값은 : " + talk.utter.utter)
                    self.DBConnect("update campaign_target_list_tb set task='task"+str(sds_temp+1)+"' where contract_no = '" + seq + "';")
                    sds_res = self.Sds.Talk(talk.utter.utter, session_id, model, product_code)
                    if tasknumber == 13:
                        pass
                    else:
                        talk.utter.utter = "$task"+ str(sds_temp+1) +"$"
                        print("utter가 들어간 값은 : " + talk.utter.utter)
                        self.DBConnect("update campaign_target_list_tb set task='task"+str(sds_temp+2)+"' where contract_no = '" + seq + "';")
                        sds_res = self.Sds.Talk(talk.utter.utter, session_id, model, product_code)

        print(sds_res)
        #print("===============test=============")

        original_answer = sds_res['response']
        answer_engine = "SDS"
        engine_path.append("SDS")

        #original_answer = self.unknown_answer()
        #첫 SDS 답변 입력사항
        original_answer = sds_res['response']
        talk_res.response.speech.utter = original_answer

        #시간 테스트
        #talk_time = dbsession[0]['talk_time']
        #talk_strp = datetime.datetime.strptime(talk_time, '%Y-%m-%d %H:%M:%S')
        #talk_month = talk_strp.month
        #talk_day = talk_strp.day
        #talk_hour = talk_strp.hour
        #talk_minute = talk_strp.minute

        nextweekdic = {
            "월요일": {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1},
            "화요일": {0: 8, 1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 2},
            "수요일": {0: 9, 1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3},
            "목요일": {0: 10, 1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 4},
            "금요일": {0: 11, 1: 10, 2: 9, 3: 8, 4: 7, 5: 6, 6: 5},
            "토요일": {0: 12, 1: 11, 2: 10, 3: 9, 4: 8, 5: 7, 6: 6},
            "일요일": {0: 13, 1: 12, 2: 11, 3: 10, 4: 9, 5: 8, 6: 7}
        }

        weekdic = {
            "월요일": {0: 0, 1: -1, 2: -2, 3: -3, 4: -4, 5: -5, 6: -6},
            "화요일": {0: 1, 1: 0, 2: -1, 3: -2, 4: -3, 5: -4, 6: -5},
            "수요일": {0: 2, 1: 1, 2: 0, 3: -1, 4: -2, 5: -3, 6: -4},
            "목요일": {0: 3, 1: 2, 2: 1, 3: 0, 4: -1, 5: -2, 6: -3},
            "금요일": {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: -1, 6: -2},
            "토요일": {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 0, 6: -1},
            "일요일": {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0}
        }

        daylist = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}

        temp_list = [0, 1, 2, 3, 4, 5, 6]
        temp_list_kor = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        # 현재시간 입력
        next_month = ""
        next_day = ""
        next_part = ""
        next_hour = ""
        next_minute = ""
        #next_time = talk_time
        next_time = datetime.datetime.now()


        #시간 컨펌
        a['nextweek'] = ""
        a['morae'] = ""
        a['tomorrow'] = ""
        a['today'] = ""
        a['day'] = ""
        a['part'] = ""
        a['hour'] = ""
        a['minute'] = ""
        a['input_month'] = ""
        a['input_day'] = ""
        

        if sds_res['current_task'] == 'timeAffirm':
            items = sds_res['intent.filled_slots.items']
            print(items)
            for id in items:
                a[id[0]] = id[1]
                print(id)
            if a['nextweek'] == "" : slot_nextweek = ""
            elif a['nextweek'] == '돌아오는' : slot_nextweek = "다음" 
            else: slot_nextweek = a['nextweek']
            if a['morae'] == "" : slot_morae = ""
            else: slot_morae = a['morae']
            if a['input_month'] == "" : slot_input_month = ""
            else: slot_input_month = a['input_month']
            if a['input_day'] == "" : slot_input_day = ""
            else: slot_input_day = a['input_day']
            if a['tomorrow'] == "" : slot_tomorrow = ""
            else: slot_tomorrow = a['tomorrow']
            if a['today'] == "" : slot_today = ""
            else: slot_today = a['today']
            if a['day'] == "" : slot_day = ""
            else: slot_day = a['day']
            if a['part'] == "" : slot_part = ""
            elif a['part'] == '저녁' or  a['part'] == '밤': slot_part = "오후" 
            elif a['part'] == '아침' or  a['part'] == '새벽': slot_part = "오전" 
            else: slot_part = a['part']
            if a['hour'] == "" : slot_hour = ""
            else: slot_hour = a['hour']
            if a['minute'] == "" : slot_minute = ""
            elif a['minute'] == "반": slot_minute = "30"
            else: slot_minute = a['minute']
            ### 시를 수정하는 로직
            print ('첫번쨰 시 출력' + str(slot_hour))
            re_input = str(slot_hour)
            re_input = re_input.replace(' ','')
            hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', re_input.decode('utf-8')))
            print(hanCount)
            if hanCount >= 1:
                print("여기에 들어왔따")
                slot_hour = self.change_bu(re_input)
                hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', slot_hour.decode('utf-8')))
                if hanCount >= 1:
                    slot_hour = self.change(re_input)
                else:
                    print('시에서 1차 분류 거치고 한글은 더이상 없는 것 같네요')
                    pass
            else:
                print('시에서는 한글은 없는 것 같네요')
                pass
            print ('두번쨰 시 출력' + str(slot_hour))
#            slot_hour = int(slot_hour)
            ### 분를 수정하는 로직
            re_input = str(slot_minute)
            re_input = re_input.replace(' ','')
            hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', re_input.decode('utf-8')))
            if hanCount >= 1:
                slot_minute = self.change_bu(re_input)
                hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', slot_minute.decode('utf-8')))
                if hanCount >= 1:
                    slot_minute = self.change(re_input)
                else:
                    print('분에서 1차 분류 거치고 한글은 더이상 없는 것 같네요')
                    pass
            else:
                print('분에서는 한글은 없는 것 같네요')
                pass
#            slot_minute = int(slot_minute)
            print ("slot_nextweek : " + str(slot_nextweek))
            print ("slot_morae : " + str(slot_morae))
            print ("slot_tomorrow : " + str(slot_tomorrow))
            print ("slot_today : " + str(slot_today))
            print ("slot_day : " + str(slot_day))
            print ("slot_part : " + str(slot_part))
            print ("slot_hour : " + str(slot_hour))
            print ("slot_minute : " + str(slot_minute))
            print("시이이이이이작")
            if slot_input_month is not None and slot_input_month != "":
                if slot_input_day is not None and slot_input_day != "":
                    print ("일월 입력")
                    next_time = next_time.replace(month=int(slot_input_month), day=int(slot_input_day))
                elif slot_input_day is None and slot_input_day == "":
                    print ("월은 있는데 일은 입력되지 않았습니다.")
                    talk.utter.utter = "$dayMiss$"
            elif slot_input_month is None or slot_input_month == "":
                if slot_input_day is not None and slot_input_day != "":
                    next_time = next_time.replace(day=int(slot_input_day))
                    
                    #print("일은 있는데 월을 입력하지 않았습니다.")
                    #talk_utter.utter = "$dayMiss$" 
                else:
                    if slot_nextweek == "이번":
                        if slot_day in temp_list_kor:
                            print("여기에 들어와씀")
                            b = int(weekdic[str(slot_day)][next_time.weekday()])
                            #next_time = next_time.replace(day=next_time.day + b)
                            plus_time = datetime.timedelta(days=b)
                            next_time = next_time + plus_time
                        elif slot_day is None or slot_day == "":
                            talk.utter.utter = "$dayMiss$"
                        else:
                            talk.utter.utter = "$dayMiss$"
                    elif slot_nextweek == "다음":
                        print("다음 적용")
                   # if test_time.weekday() in temp_list:
                        if slot_day in temp_list_kor:
                            print("111111111111111111111 : " + str(slot_day) + str(next_time.weekday()))
                            b = int(nextweekdic[str(slot_day)][next_time.weekday()])
                            print (b)
                            #next_time = next_time.replace(day=next_time.day + int(b))
                            plus_time = datetime.timedelta(days=b)
                            next_time = next_time + plus_time
                        elif slot_day is None or slot_day == "":
                            b = 7
                            #next_time = next_time.replace(day=next_time.day + int(b))
                            plus_time = datetime.timedelta(days=b)
                            next_time = next_time + plus_time
                        else:
                            talk.utter.utter = "$dayMiss$"
                            print("쓸대없는 요일을 말씀하셨습니다.")
                             #일자 더하기
                    elif slot_morae == "모레" or slot_morae == "내일 모레" or slot_morae == "내일모레":
                        b = 2
                        plus_time = datetime.timedelta(days=b)
                        next_time = next_time + plus_time
                        #next_time = next_time.replace(day=next_time.day + b)
                    elif slot_tomorrow == "내일":
                        print("들어와씀")
                        b = 1
                        plus_time = datetime.timedelta(days=b)
                        next_time = next_time + plus_time
                        #next_time = next_time.replace(day=next_time.day + b)
                    elif slot_today == "오늘":
                        b = 0
                        plus_time = datetime.timedelta(days=b)
                        next_time = next_time + plus_time
                        #next_time = next_time.replace(day=next_time.day + b)
                    elif slot_nextweek == "" or slot_nextweek is None:
                        pass
                    else:
                        talk.utter.utter = "$inputMiss$"
                        print ("일정을 입력을 하시지 않았습니다. 다시 입력해주세요.")
                
            #elif slot_day[daylist] in temp_list:

            if slot_hour is None or slot_hour == "":
                if slot_minute is None or slot_minute == "":
                    print(talk_time.hour + talk_time.minute)
                    next_time = next_time.replace(hour=int(talk_time.hour), minute=int(talk_time.minute))
                    pass
                else:
                    print("시를 말씀해주시지 않았습니다.")
                    talk.utter.utter = "$hourMiss$"
            else:
                if slot_minute is None or slot_minute == "":
                    print("3333333333333333333333")
                    next_time = next_time.replace(hour=int(slot_hour), minute = 00)
                else:
                    print("4444444444444444444444")
                    print ("slot_hour + :"+ str(slot_hour))
                    print ("slot_minute + :"+ str(slot_minute))
                    next_time = next_time.replace(hour=int(slot_hour), minute=int(slot_minute))

            next_month = next_time.month
            next_day = next_time.day

            if slot_part == "오전" or slot_part == "오후":
                next_part = slot_part
                if slot_hour is None or slot_hour == "":
                    print("나와ㄸ따다ㅣㅏㅓ아러나리어나리어나리어내ㅏ")
                    talk.utter.utter = "$hourMiss$"
                    next_hour = next_time.hour
                    #next_time.minute = ""
                else:
                    next_hour = next_time.hour
                    
            else:
                if next_time.hour > 12 and next_time.hour < 24:
                    next_part = "오후"
                    next_hour = next_time.hour - 12
                elif next_time.hour == 12:
                    next_part = "오후"
                    next_hour = 12
                elif next_time.hour > 0 and next_time.hour < 12:
                    next_part = "오전"
                    next_hour = next_time.hour
                elif next_time.hour == 0:
                    next_part = "오전"
                    next_hour = next_time.hour



            next_minute = next_time.minute
            #slot_hour = self.readNumberHour((a['hour']))
            #text_output = self.readNumber(31)
            #talk_res.response.speech.utter = text_output
            print(next_time)
            #next_month = ""
            #next_day = ""
            #next_part = ""
            #next_hour = ""
            #next_minute = ""
        if sds_res['current_task'] == 'timeAffirm':
            if talk.utter.utter == "$hourMiss$" or talk.utter.utter == "$dayMiss$":
                print("dcdddddddddddddddddddddddddddddddddddd")
                sds_res = self.Sds.Talk(talk.utter.utter, session_id, model, product_code)
            else:
                print("===============test=============")
                print("next_month : " + str(next_month))
                print("next_day : " + str(next_day))
                print("next_part : " + str(next_part))
                print("next_hour : " + str(next_hour))
                print("next_minute : " + str(next_minute))
                print("===============test=============")
                talk_res.response.speech.utter = "말씀하신 통화가능 시간이 " + self.readNumberMinute(next_month) +"월"+ self.readNumberMinute(next_day) + "일 "+str(next_part) +", " +  self.readNumberHour(next_hour) + "시 "+ self.readNumberMinute(next_minute) + "분이 맞습니까?"
                self.DBConnect("update campaign_target_list_tb set next_time='"+str(next_time)+"' where contract_no = '" + seq + "';")
            #talk_res.response.speech.utter = "말씀하신 통화가능 시간이 " + next_month +"월"+ next_day + "일 "+next_part +", " +  next_hour + "시 "+ next_minute + "분이 맞습니까?"
            #말씀하신 일정이 11월 19일 오전 3시 30분이 맞습니까?
        #if sds_res['current_task'] == 'timeEnd':
            #self.DBConnect("update hc_hh_campaign_score set next_time='"+str(next_time)+"' where contract_no = '" + seq + "';")





        #질문 수정사항
        sds_intent = self.Sds.GetIntent(talk.utter.utter, model)
        #task1
        if sds_res['current_task'] == 'task1':
            talk_res.response.speech.utter = "안녕하십니까?, 현대해상 고객센터입니다, " + user_name + "고객님 되십니까?"
        #task2
        if sds_res['current_task'] == 'task2':
            talk_res.response.speech.utter = "" + self.readNumberMinute(join_month) + "월" + self.readNumberMinute(join_day) +"일, 저희 현대해상 "+prod_name+"을 가입해 주셔서, 진심으로 감사드립니다, 가입하실때, 상품의 중요한 사항이 제대로 설명되었는지, 확인드리고자 연락드렸습니다, 소요시간은 약 삼분정도인데, 잠시 통화 가능하십니까?"
        #PRIVACY1
        if sds_res['current_task'] == 'PRIVACY1':
            talk_res.response.speech.utter = "지금부터 진행하는 내용은 고객님의 권리보호를 위해 녹음되며, 답변하신 내용은 향후 민원 발생시, 중요한 근거자료로 활용되오니, 정확한 답변 부탁드리겠습니다, 먼저 본인확인을 위해 주민번호 여섯자리를 말씀해주세요."
        #PRIVACY2
        if sds_res['current_task'] == 'PRIVACY2':
            talk_res.response.speech.utter = "말씀해주셔서 감사합니다, 고객님의 주소는 " + str(privacy_add1) + ", " + str(privacy_add2) + "로 확인 되는데 맞으십니까?"
        #PRIVACY3
        if sds_res['current_task'] == 'PRIVACY3':
            talk_res.response.speech.utter = "말씀해주셔서 감사합니다, 고객님의 주소는 " + str(privacy_add1) + " 으로 확인되는데요, 나머지 주소는 어떻게 되십니까?"
        # ask3
        if sds_res['current_task'] == 'task3':
            talk_res.response.speech.utter = "확인 감사드립니다, 계약하실 때 계약자 " + insured_contractor + "님께서 청약서, 상품설명서, 개인정보처리 동의서에 직접 서명하셨습니까?"
        # task4
        if sds_res['current_task'] == 'task4':
            talk_res.response.speech.utter = "타인의 사망을 보장 해주는 계약의 경우 보험대상자도 반드시 서면동의를 해주셔야 하는데요, 피보험자 "+ insured_person +" 님도 직접 서명하셨습니까?"
        # task8
        if sds_res['current_task'] == 'task8':
            if insured_closeproduct == 'Y':
                talk_res.response.speech.utter = "중도해지 또는 만기시, 환급금이 납입한 보험료보다 적을 수 있다는 설명을 들으셨습니까?"
            else:
                talk_res.response.speech.utter = "보험료 납입기간 중 중도 해지시, 해지환급금이 지급되지 않는다는 설명을 들으셨나요?"
        # task9
        if sds_res['current_task'] == 'task9':
            talk_res.response.speech.utter = task9_info + "화재벌금 또는 과실 치사상 벌금 담보 등은 중복가입시 보험금을 중복해서 받으실 수 있다고 설명 들으셨다면 중복, 실제지급액을 한도로 비례보상 된다는 설명을 들으셨다면 비례를 말씀해주세요."
            if sds_intent == "unknown":
                talk_res.response.speech.utter = "화재벌금 담보는 중복 가입시 비례보상됩니다, 화재벌금 또는 과실 치사상 벌금 담보 등은 중복가입시 보험금을 중복해서 받으실 수 있다고 설명 들으셨다면 중복, 실제지급액을 한도로 비례보상 된다는 설명을 들으셨다면 비례를 말씀해주세요."
            elif sds_intent == "affirm" or sds_intent == "negate":
                talk_res.response.speech.utter = "화재벌금 또는 과실 치사상 벌금 담보 등은 중복가입시 보험금을 중복해서 받으실 수 있다고 설명 들으셨다면 중복, 실제지급액을 한도로 비례보상 된다는 설명을 들으셨다면 비례를 말씀해주세요."
        #time        
        if sds_res['current_task'] == 'time':
            talk_res.response.speech.utter = "그럼 가능하신 시간을 알려주시면 다시 연락드리겠습니다,주말도 가능하니, 편하신 요일과 시간을,말씀해주세요"
        #time_end       
        if sds_res['current_task'] == 'timeEnd':
            talk_res.response.speech.utter = "네 고객님, 말씀하신 시간에 다시 연락을 드리겠습니다, 현대해상 고객센터였습니다, 감사합니다. $callback$"
        # task11
        if sds_res['current_task'] == 'task11':
            talk_res.response.speech.utter = task11_info + "일상생활배상책임 담보는 중복가입시 보험금을 중복해서 받으실 수 있다고 설명 들으셨다면 중복, 실제지급액을 한도로 비례보상 된다는 설명을 들으셨다면 비례를 말씀해주세요."
            if sds_intent == "unknown":
                talk_res.response.speech.utter = "일상생활배상책임 담보는 중복 가입시 비례보상됩니다, 일상생활배상책임 담보는 중복가입시 보험금을 중복해서 받으실 수 있다고 설명 들으셨다면 중복, 실제지급액을 한도로 비례보상 된다는 설명을 들으셨다면 비례를 말씀해주세요."
            elif sds_intent == "affirm" or sds_intent == "negate":
                talk_res.response.speech.utter = "일상생활배상책임 담보는 중복가입시 보험금을 중복해서 받으실 수 있다고 설명 들으셨다면 중복, 실제지급액을 한도로 비례보상 된다는 설명을 들으셨다면 비례를 말씀해주세요."
        # task13
        if sds_res['current_task'] == 'task13':
            talk_res.response.speech.utter = task13_info+ "법률비용 담보는 중복가입시 보험금을 중복해서 받으실 수 있다고 설명 들으셨다면 중복, 실제지급액을 한도로 비례보상 된다는 설명을 들으셨다면 비례를 말씀해주세요."
            if sds_intent == "unknown":
                talk_res.response.speech.utter = "법률비용 담보는 중복 가입시 비례보상됩니다, 법률비용 담보는 중복가입시 보험금을 중복해서 받으실 수 있다고 설명 들으셨다면 중복, 실제지급액을 한도로 비례보상 된다는 설명을 들으셨다면 비례를 말씀해주세요."
            elif sds_intent == "affirm" or sds_intent == "negate":
                talk_res.response.speech.utter = "법률비용 담보는 중복가입시 보험금을 중복해서 받으실 수 있다고 설명 들으셨다면 중복, 실제지급액을 한도로 비례보상 된다는 설명을 들으셨다면 비례를 말씀해주세요."
        # task13
        if sds_res['current_task'] == 'time':
            if sds_intent == "hourmiss":
                talk_res.response.speech.utter = "통화 가능 시를 말씀해주시지 않았습니다.통화가능 시를 말씀해주세요."
            if sds_intent == "daymiss":
                talk_res.response.speech.utter = "통화 가능 요일을 말씀해주시지 않았습니다.통화가능 요일을 말씀해주세요."
        #task14       
        if sds_res['current_task'] == 'task14':
            talk_res.response.speech.utter = "네 고객님, 소중한시간 내주셔서 감사합니다. 현대해상 고객센터였습니다. $complete$"


        print("[ANSWER]: " + original_answer)
        #print("[SESSION_KEY] :" + )
        print("[ENGINE]: " + answer_engine)

        #위치 전송
        #self.DBConnect("update hc_hh_campaign_score set task='"+ sds_res['current_task'] + "' where contract_no = '" + seq + "';")




        return talk_res


    # 1~999
    def readNumberMinute(self,n):

        n = int(n)
        units = '일,십,백,천'.split(',')
        nums = '일,이,삼,사,오,육,칠,팔,구'.split(',')
        result = []
        i = 0
        while n > 0:
            n, r = divmod(n, 10)
            if r == 1:
                result.append(str(units[i]))
            elif i == 0 and r > 0:
                result.append(nums[r - 1])
            elif r > 0:
                result.append(nums[r - 1] + str(units[i]))
            i += 1
        if len(result) == 0:
            result.append("영")
        return ''.join(result[::-1])

    def readNumberHour(self,n):
        n = int(n)
        units = '한,열,백,천'.split(',')
        nums = '한,두,세,네,다섯,여섯,일곱,어덟,아홉'.split(',')
        #    units = list('일십백천')
        #    nums = list('일이삼사오육칠팔구')
        #    units = ['일', '십', '백', '천']
        #    nums = ['일', '이' ,'삼' ,'사' ,'오' ,'육' ,'칠' ,'팔' ,'구']
        result = []
        i = 0
        while n > 0:
            n, r = divmod(n, 10)
            if r == 1:
                result.append(str(units[i]))
            elif i == 0 and r > 0:
                result.append(nums[r - 1])
            elif r > 0:
                result.append(nums[r - 1] + str(units[i]))
            i += 1
        if len(result) == 0:
            result.append("영")
        return ''.join(result[::-1])
    def change_bu(self,input):
        b = {
            '한': '1',
            '두': '2',
            '세': '3',
            '네': '4',
            '다섯': '5',
            '여섯': '6',
            '일곱': '7',
            '여덟': '8',
            '아홉': '9',
            '열': '10',
            '열한': '11',
            '열두': '12',
            '열세': '13',
            '열네': '14',
            '열다섯': '15',
            '열여섯': '16',
            '열일곱': '17',
            '열여덟': '18',
            '열아홉': '19',
            '스물': '20',
            '스물한': '21',
            '스물두': '22',
            '스물세': '23',
            '스물네': '24'
        }
        text = {'스물네', '스물세', '스물두', '스물한', '스물', '열아홉', '열여덟', '열일곱', '열여섯', '열다섯', '열네', '열세', '열두', '열한', '열', '아홉','여덟', '일곱', '여섯', '다섯', '네', '세', '두', '한'}
        for t in text:
            if input.find(t) >= 0:
                input = input.replace(t, b[t])
            else:
                pass
        return input
    def change(self,input):
        kortext = '영일이삼사오육칠팔구'
        dic = {'십': 10, '백': 100, '천': 1000, '만': 10000, '억': 100000000, '조': 1000000000000}
        result = 0
        tmpResult = 0
        num = 0
        for i in range(0,len(input)):
            token = input[i]
            check = kortext.find(input[i])

            if check == -1:
                if '만억조'.find(token) == -1:
                    if num != 0:
                        tmpResult = tmpResult + num * dic[token]
                    else:
                        tmpResult = tmpResult + 1 * dic[token]

                else:
                    tmpResult = tmpResult + num
                    if tmpResult != 0:
                        result = result + tmpResult * dic[token]
                    else:
                        result = result + 1 * dic[token]
                    tmpResult = 0

                num = 0
            else:
                num = check
        return result + tmpResult + num


    def unknown_answer(self):
        """
        리스트에서 랜덤으로 Unknown 답변 출력.
        """
        unknown_text = ['죄송해요, 제가 잘 못 알아 들었어요. 키워드 위주로 다시 질문해주시겠어요?',
                        '답변을 찾을 수 없습니다. 다른 질문을 해주시면 성실히 답변해 드리겠습니다. ']
        return random.choice(unknown_text)


    def Close(self, req, context):
        print 'V3 ', 'Closing for ', req.session_id, req.agent_key
        talk_stat = provider_pb2.TalkStat()
        talk_stat.session_key = req.session_id
        talk_stat.agent_key = req.agent_key

        return talk_stat

    def EventT(self, empty, context):
        print 'V3 ', 'DA Version 3 EventT', 'called'

        # DO NOTHING
        return empty_pb2.Empty()

    def Open(self, req, context):
        print 'V3 ', 'Open', 'called'
        # req = talk_pb2.OpenRequest()
        event_res = talk_pb2.OpenResponse()
        event_res.code = 1000000
        event_res.reason = 'success'
        answer_meta = struct.Struct()

        answer_meta["play1"] = "play1"
        answer_meta["play2"] = "play2"
        answer_meta["play3"] = "play3"

        answer_meta.get_or_create_struct("audio1")["name"] = "media_play1"
        answer_meta.get_or_create_struct("audio1")["url"] = "htpp://101.123.212.321:232/media/player_1.mp3"
        answer_meta.get_or_create_struct("audio1")["duration"] = "00:10:12"

        answer_meta.get_or_create_struct("audio2")["name"] = "media_play2"
        answer_meta.get_or_create_struct("audio2")["url"] = "htpp://101.123.212.321:232/media/player_1.mp3"
        answer_meta.get_or_create_struct("audio2")["duration"] = "00:00:15"

        event_res.meta.CopyFrom(answer_meta)
        answer_context = struct.Struct()
        answer_context["context1"] = "context_body1"
        answer_context["context2"] = "context_body2"
        answer_context["context3"] = "context_body3"
        event_res.context.CopyFrom(answer_context)

        # DO NOTHING
        return event_res

    def Event(self, req, context):
        print 'V3 ', 'Event', 'called'
        # req = talk_pb2.EventRequest()

        event_res = talk_pb2.EventResponse()
        event_res.code = 10
        event_res.reason = 'success'

        answer_meta = struct.Struct()
        answer_meta["meta1"] = "meta_body_1"
        answer_meta["meta2"] = "meta_body_2"
        event_res.meta.CopyFrom(answer_meta)

        answer_context = struct.Struct()
        answer_context["context1"] = "context_body1"
        answer_context["context2"] = "context_body2"
        answer_context["context3"] = "context_body3"
        event_res.context.CopyFrom(answer_context)

        return event_res

def serve():
    parser = argparse.ArgumentParser(description='CMS DA')
    parser.add_argument('-p', '--port',
                        nargs='?',
                        dest='port',
                        required=True,
                        type=int,
                        help='port to access server')
    args = parser.parse_args()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    talk_pb2_grpc.add_DialogAgentProviderServicer_to_server(
        EchoDa(), server)

    listen = '[::]' + ':' + str(args.port)
    server.add_insecure_port(listen)

    server.start()

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
