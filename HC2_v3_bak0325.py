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
from google.protobuf.json_format import MessageToJson
import time
import syslog
import pymysql
import datetime
import re
import json

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
from custom_hs.HC_Func import FUNC

# echo_simple_classifier = {
#    "echo_test": {
#        "regex": [
#            "."
#        ]
#    }

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
Session_Value = []
_NOTHING_FOUND_INTENT_ = "의도를 찾지 못했습니다."
model = 'Happy_Call_HH2'

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
        self.func = FUNC()

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

        ######### 세션 카운트 지정
#        logic_count = (
#                {
#                    "task1" : "0",
#                    "task2" : "0",
#                    "task3" : "0",
#                    "task4" : "0",
#                    "task5" : "0",
#                    "task6" : "0",
#                    "task7" : "0",
#                    "task8" : "0",
#                    "task9" : "0",
#                    "task9_1" : "0",
#                    "time" : "0",
#                    "timeaffirm" : "0",
#                    "PRIVACY1" : "0",
#                    "PRIVACY1_1" : "0",
#                    "privacy1_1affirm" : "0",
#                    "PRIVACY2" : "0"
#                }
#            )
        
        session_data = struct.Struct()
        session_data['id'] = session_id
        session_data['task1'] = '0'
        session_data['task2'] = '0'
        session_data['task3'] = '0'
        session_data['task4'] = '0'
        session_data['task5'] = '0'
        session_data['task6'] = '0'
        session_data['task7'] = '0'
        session_data['task8'] = '0'
        session_data['task9'] = '0'
        session_data['task9_1'] = '0'
        session_data['time'] = '0'
        session_data['timeaffirm'] = '0'
        session_data['PRIVACY1'] = '0'
        session_data['PRIVACY1_1'] = '0'
        session_data['PRIVACY1_1affirm'] = '0'
        session_data['PRIVACY2'] = '0'
        result.response.session_update.context.CopyFrom(session_data)

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

    def db_dml(self, query, sql_args):
        conn = pymysql.connect(user="aicc",
                               password="ggoggoma",
                               host="aicc-bqa.cjw9kegbaf8s.ap-northeast-2.rds.amazonaws.com",
                               database="happycall",
                               charset="utf8",
                               use_unicode=False)
        curs = conn.cursor(pymysql.cursors.DictCursor)
        #query = "select * from test;"
        print(query)
        try:
            curs.executemany(query, sql_args)
        except:
            conn.rollback()
        else:
            conn.commit()
        finally:
            print("query good!")
            curs.close()
            conn.close()


    def Talk(self, talk, context):

        a = {}

        ##m2u으로 시작
        talk.utter.utter = talk.utter.utter + ";$callSeq=93$call_Id=3004"
        print("talk : ", talk.utter.utter)
        #seq = talk.utter.utter[talk.utter.utter.index(";$callSeq")+10:talk.utter.utter.index(";$callSeq")+11]
        seq = talk.utter.utter[talk.utter.utter.index(";$callSeq")+10:talk.utter.utter.index("$call_")]
        call_id = talk.utter.utter[talk.utter.utter.index("$call_Id")+9:]
        print("", str(seq) + "," + str(call_id))
#        phoneNum = self.DBConnect("select cust_tel_no,session_reset from campaign_target_list_tb where contract_no = '" + seq + "';")
#        reset_count = phoneNum[0]['session_reset']
#        phoneNum = phoneNum[0]['cust_tel_no']
#        if reset_count == '1':
#            pass
#        else:
#            self.DBConnect("update campaign_target_list_tb set session_reset='1' where contract_no = '" + seq + "';")
#            self.DBConnect("update task_logic set PRIVACY1=0, task1=0,task2=0,task3=0,task4=0,task5=0,task6=0,task7=0,task8=0,task9=0,task9_1=0,PRIVACY1_1=0,PRIVACY2=0,privacy1_1affirm=0,time=0,timeaffirm=0 where contract_no = "+seq+";")
#            task_list = ['task1','task2','PRIVACY1','time','timeAffirm','task3','task4']
#            sql_args = list()
#            for i in task_list:
#                seq_id_db = self.DBConnect("select seq from hc_hh_campaign_info where camp_id=2 and task = '" + i + "';")
#                #print (camp_id_db)
#                seq_id = str(seq_id_db[0]['seq'])
#                sql_args.append((call_id, seq, seq_id, i))
#                #self.DBConnect("insert into hc_hh_campaign_score (call_id, contract_no, info_seq, info_task, task_value) values ('"+call_id+"','"+seq+"','"+seq_id+"','"+i +"',null);")
#            self.db_dml("insert into hc_hh_campaign_score (call_id, contract_no, info_seq, info_task, task_value) values ( %s, %s, %s, %s, null);", sql_args)
            
        uttertext = talk.utter.utter[talk.utter.utter.find(";$callSeq"):]
        talk.utter.utter = talk.utter.utter.replace(uttertext,"")

        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print("talk : ", talk.utter.utter)
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
       
        # SDS.dp.slots["product_code"] = "A"
        session_id = talk.session.id
        dbsession = self.DBConnect("select session_value,cust_tel_no,cust_nm,join_time,talk_time,insured_contractor,insured_person,insured_closeproduct,address_main,address_sub,product_code1, product_code2, product_code3, cust_ssn, prod_name,camp_id from campaign_target_list_tb where contract_no = '" + seq + "';")
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
        product_code1 = dbsession[0]['product_code1']
        product_code2 = dbsession[0]['product_code2']
        product_code3 = dbsession[0]['product_code3']
        prod_name = dbsession[0]['prod_name']
        prod_name = '무배당 게속받는 암보험'
        cust_ssn = dbsession[0]['cust_ssn']
        camp_id = dbsession[0]['camp_id']
        cust_ssn = cust_ssn[0:6]

        ##세션 고정 시키기
#        if dbsession[0]['session_value'] is None:
#            dbsessioncode = talk.session.id
#            self.DBConnect("update campaign_target_list_tb set session_value = '" + str(dbsessioncode) + "' where contract_no = '" + seq + "';")
#            session_id = dbsessioncode
#        else:
#            session_id = int(dbsession[0]['session_value'])

        talk_res = talk_pb2.TalkResponse()


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
        unknown_count = 0

#        # SDS
        dbtask = self.DBConnect("select task from campaign_target_list_tb where contract_no = '" + seq + "';")
        task = dbtask[0]['task']
        sds_res = self.Sds.Talk(talk.utter.utter, session_id, model)
#        if sds_res['current_task'] == 'task2':
#            dic = dict(talk.session.context)
#            count_dic = json.loads(dic.get('count'))
#
#            print(count_dic)
#            count_dic[0]['task1'] = "5555"
#            session_data = struct.Struct()
#            session_data['id'] = talk.session.id
#            session_data['count'] = count_dic
#            talk_res.response.session_update.context.CopyFrom(session_data)
#        elif sds_res['current_task'] == 'task3':
#            print("$" * 70)
#            print(dict(talk.session.context))
#            print("$" * 70)
##            count_dic = json.loads(dict(talk.session.context).get('count'))
#            dic = json.loads(MessageToJson(talk.session.context))
#            print(dic)
#            count_dic = dic.get('count')[0].get('task1')
##            print(count_dic[0].get('task1'))
#            print(count_dic)
        if sds_res['current_task'] == 'task2':
#            dic = dict(talk.session.context)
#            dic['task1'] = '5555'
#
#            print(dic)
#            session_data = struct.Struct()
#            session_data['id'] = talk.session.id
#            session_data = dic

            session_data = talk.session.context
            session_data['id'] = talk.session.id
            session_data['task1'] = '5555'
            print(session_data)
            talk_res.response.session_update.context.CopyFrom(session_data)
        elif sds_res['current_task'] == 'task3':
            print("$" * 70)
            print(dict(talk.session.context))
            print("$" * 70)
#            count_dic = json.loads(dict(talk.session.context).get('count'))
            dic = json.loads(MessageToJson(talk.session.context))
            print(dic)
            count_dic = dic.get('count')[0].get('task1')
#            print(count_dic[0].get('task1'))
            print(count_dic)
            
            






        task_list = ['task1','task2','task3','task4','task5','PRIVACY1','PRIVACY2']
        for i in task_list:
          if sds_res['current_task'] == i:
              sds_intent = self.Sds.GetIntent(talk.utter.utter, model)
              session_data = talk.session.context
              session_count = int(session_data[i])
#              dic = json.loads(MessageToJson(talk.session.context))
#              print(dic.get('count')[0])
#              print(type(dic.get('count')[0]))
#              session_count  = dic.get('count')[0].get(i)
#              session_count = int(session_count)
        

#              DBcount = self.DBConnect("select "+i+" from task_logic where contract_no = '" + seq  + "';")
#              count = DBcount[0][i]
              if sds_intent == 'unknown' or sds_intent == 'again':
#                  DBcount = self.DBConnect("select "+i+" from task_logic where contract_no = '" + seq  + "';")
#                  count = DBcount[0][i]
                  session_count = session_count + 1
                  session_data[i] = session_count
                  print('**************************' + str(session_data[i]))
                  talk_res.response.session_update.context.CopyFrom(session_data)
                  #dic = json.loads(MessageToJson(talk.session.context))
                  #count_dic = dic.get('count')[0].get(i)
#                  session_data = struct.Struct()
#                  session_data['id'] = talk.session.id
#                  session_data['count'] = 
#                  talk_res.response.session_update.context.CopyFrom(session_data)

#                  self.DBConnect("update task_logic set "+i+"='"+str(count)+"' where contract_no = '" + seq + "';")
                  if int(session_count) >= 2:
                      seq_id_db = self.DBConnect("select seq from hc_hh_campaign_info where task = '" + sds_res['current_task'] + "';")
                      #print (camp_id_db)
                      seq_id = str(seq_id_db[0]['seq'])
                      talk.utter.utter = "$"+i+"$"
                      self.DBConnect("update hc_hh_campaign_score set task_value = '모름' where contract_no = '" +seq+ "' and info_task = '"+ task +"';")
                     # self.DBConnect("insert into hc_hh_campaign_score (call_id, contract_no, info_seq, info_task, task_value) values ('"+call_id+"','"+seq+"','"+seq_id+"','"+sds_res['current_task'] +"','모름')");
                      self.DBConnect("update campaign_target_list_tb set task='"+sds_res['current_task']+"' where contract_no = '" + seq + "';")
                      #unknown_count = 1
                 
                      sds_res = self.Sds.Talk(talk.utter.utter, session_id, model)


        #sds_res = self.Sds.Talk(talk.utter.utter, session_id, model)

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
            seq_id_db = self.DBConnect("select seq from hc_hh_campaign_info where camp_id = '"+str(camp_id)+"' and task = '" + task  + "';")
         #   print (camp_id_db)
            seq_id = str(seq_id_db[0]['seq'])
            if sds_intent == 'affirm':
                self.DBConnect("update hc_hh_campaign_score set task_value = 'Y' where contract_no = '" +seq+ "' and info_task = '"+ task +"';")
            elif sds_intent == 'negate':
                self.DBConnect("update hc_hh_campaign_score set task_value = 'N' where contract_no = '" +seq+ "' and info_task = '"+ task +"';")
            elif sds_intent == 'overlap' or sds_intent == 'noproportion':
                self.DBConnect("update hc_hh_campaign_score set task_value = '중복' where contract_no = '" +seq+ "' and info_task = '"+ task +"';")
            elif sds_intent == 'nooverlap' or sds_intent == 'proportion':
                self.DBConnect("update hc_hh_campaign_score set task_value = '비례' where contract_no = '" +seq+ "' and info_task = '"+ task +"';")
            elif sds_intent == 'unknown' or sds_intent == 'again':
                pass
            elif unknown_count == 1:
                pass
            else:
                if task == 'PRIVACY1' or task == 'time':
                    self.DBConnect("update hc_hh_campaign_score set task_value = '입력' where contract_no = '" +seq+ "' and info_task = '"+ task +"';")

        self.DBConnect("update campaign_target_list_tb set task='"+ sds_res['current_task'] + "' where contract_no = '" + seq + "';")

        print("SDS Start!")

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
        a['input_year'] = ""
        a['input_six'] = ""

        if sds_res['current_task'] == 'timeAffirm':
            items = sds_res['intent.filled_slots.items']
            print(items)
            for id in items:
                a[id[0]] = id[1]
                print(id)
            if a['input_year'] == "" : input_year = ""
            else: input_year = a['input_year']
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
            re_input = re_input.replace('시','')
#           sds_intent = self.Sds.GetIntent(talk.utter.utter, model)
            slot_hour = self.func.convert_time(re_input)


            print ('두번쨰 시 출력' + str(slot_hour))
#            slot_hour = int(slot_hour)
            ### 분를 수정하는 로직
            re_input = str(slot_minute)
            print ('들어온 분은 : '+ str(slot_minute))
            re_input = re_input.replace(' ','')
            re_input = re_input.replace('분','')
            slot_minute = self.func.convert_time(re_input)
            
            ############ 결과 값 받기
            (next_time, next_month, next_day, next_part, next_hour, next_minute) = \
            self.func.next_call_schedule(slot_nextweek, slot_morae, slot_input_month,\
            slot_input_day, slot_tomorrow, slot_today, slot_day, slot_part,slot_hour, slot_minute)



        if sds_res['current_task'] == 'timeAffirm':
            if talk.utter.utter == "$hourMiss$" or talk.utter.utter == "$dayMiss$":
                print("dcdddddddddddddddddddddddddddddddddddd")
                sds_res = self.Sds.Talk(talk.utter.utter, session_id, model)
            else:
                print("===============test=============")
                print("next_month : " + str(next_month))
                print("next_day : " + str(next_day))
                print("next_part : " + str(next_part))
                print("next_hour : " + str(next_hour))
                print("next_minute : " + str(next_minute))
#                print("===============test=============")
                if int(next_minute) == 0 or next_minute == '':
                        talk_res.response.speech.utter = "말씀하신 통화가능 시간이 " \
                        + self.func.readNumberMinute(next_month) +"월"+ \
                        self.func.readNumberMinute(next_day) + "일 "\
                        +str(next_part) +", " +  self.func.readNumberHour(next_hour) + "시가 맞습니까?"
                else:
                        talk_res.response.speech.utter = "말씀하신 통화가능 시간이 " \
                        + self.func.readNumberMinute(next_month) +"월"\
                        + self.func.readNumberMinute(next_day) + "일 "+str(next_part) +", " \
                        + self.func.readNumberHour(next_hour) + "시 "\
                        + self.func.readNumberMinute(next_minute) + "분이 맞습니까?"
                    
                self.DBConnect("update campaign_target_list_tb set next_time='"+str(next_time)+"' where contract_no = '" + seq + "';")

        print ("죄종답변 intent: "+ sds_intent)
        #task1
        if sds_res['current_task'] == 'task1':
            if (sds_intent != 'affirm' and sds_intent != 'negate') and len(talk.utter.utter) >= 15:
                talk_res.response.speech.utter = "통화종료. $unConnected$"
            elif sds_intent == "again":
                talk_res.response.speech.utter = "현대해상 로봇상담원입니다, \
                "+ user_name + "고객님 되시나요?"
            elif sds_intent == 'unknown':
                talk_res.response.speech.utter = "네, 또는 아니오로 답변해주세요,"
            elif sds_intent == 'negate':
                talk_res.response.speech.utter = "죄송합니다. 잘못 연락드렸습니다. \
                오늘도 행복한 하루 보내세요. $callback$"
            elif sds_intent == 'task1':
                talk_res.response.speech.utter = "상담사를 통해 다시 연락드리겠습니다, \
                현대해상 고객센터 였습니다. $callback$"
            else:
                talk_res.response.speech.utter = "안녕하십니까?, 현대해상 로봇상담원입니다. \
                " + user_name + "고객님 되십니까?"
            
        #task2
        if sds_res['current_task'] == 'task2':
            if sds_intent == 'again':
                talk_res.response.speech.utter = "가입하실때. 상품 내용이 제대로 설명되었는지. \
                확인드리고자 연락드렸습니다. 잠시 통화 가능하십니까?"
            elif sds_intent == 'unknown':
                talk_res.response.speech.utter = "네, 또는 아니오로 답변해주세요,"
            elif sds_intent == 'task2':
                talk_res.response.speech.utter = "상담사를 통해 다시 연락드리겠습니다, \
                현대해상 고객센터 였습니다. $callback$"
            else:
                talk_res.response.speech.utter = "네 고객님, 반갑습니다,"\
                + self.func.readNumberMinute(join_month) + "월" \
                + self.func.readNumberMinute(join_day) +"일, \
                저희 현대해상 "+prod_name+"을 가입해 주셔서, 진심으로 감사드립니다. \
                가입하실때, 상품의 중요한 사항이 제대로 설명되었는지,\
                확인드리고자 연락드렸습니다, 소요시간은 약 이분정도인데. 잠시 통화 가능하십니까?"

        #PRIVACY1
        if sds_res['current_task'] == 'PRIVACY1':
            if sds_intent == 'again':
                talk_res.response.speech.utter = "고객님의 성함이, "+ user_name + "고객님 맞으십니까?"
            elif sds_intent == 'unknown':
                talk_res.response.speech.utter = "네, 또는 아니오로 답변해주세요,"
            elif sds_intent == 'negate':
                talk_res.response.speech.utter = "죄송합니다만, 담당자와 통화 후, \
                다시한번 연락을 드리겠습니다, 번거롭게 해드려 죄송합니다. $callback$"
            elif sds_intent == 'privacy':
                talk_res.response.speech.utter = "죄송합니다만, 담당자와 통화 후, \
                다시한번 연락을 드리겠습니다, 번거롭게 해드려 죄송합니다. $callback$"
            else:
                talk_res.response.speech.utter = "지금부터 진행하는 내용은 고객님의\
                권리보호를 위해 녹음되며, 답변하신 내용은 향후 민원 발생시, \
                중요한 근거자료로 활용되오니, 정확한 답변 부탁드리겠습니다. "\
                + user_name + "고객님 맞으십니까"


        # task3
        if sds_res['current_task'] == 'task3':
            if sds_intent == 'again':
                talk_res.response.speech.utter = "계약자와 피보험자가 다른 계약의 경우. \
                피보험자이신 "+ insured_person +" 고객님의 계약체결에 대한 동의가 반드시 필요합니다. \
                자필서명이 정확하게 이루어지지 않은 경우. \
                무효계약으로 고객님께서 불이익을 보실 수 있습니다. \
                고객님께서 청약서에 직접 자필서명을 하셨는지요?"
            elif sds_intent == 'unknown':
                talk_res.response.speech.utter = "네, 또는 아니오로 답변해주세요,"
            else:
                talk_res.response.speech.utter = "확인 감사합니다, 질문은 총 두가지입니다.\
                계약자와 피보험자가 다른 계약의 경우. 피보험자이신 "+ insured_person +".\
                고객님의 계약체결에 대한 동의가 반드시 필요합니다.\
                자필서명이 정확하게 이루어지지 않은 경우. \
                무효계약으로 고객님께서 불이익을 보실 수 있습니다. \
                고객님께서 청약서에 직접 자필서명을 하셨는지요?"

        # task4
        if sds_res['current_task'] == 'task4':
            if sds_intent == 'again':
                talk_res.response.speech.utter = "직업, 건강상태 등 계약전 알릴의무 사항을\
                제대로 알리지 않으면 .향후 보험금 지급이 제한될 수 있는데요,\
                고객님께서 해당 내용을 정확히 확인하고 작성하셨습니까?"
            elif sds_intent == 'unknown':
                talk_res.response.speech.utter = "네, 또는 아니오로 답변해주세요,"
            else:
                talk_res.response.speech.utter = "그러셨군요, 마지막 질문입니다. \
                직업, 건강상태 등 계약전 알릴의무 사항을 제대로 알리지 않으면.\
                향후 보험금 지급이 제한될 수 있는데요, \
                고객님께서 해당 내용을 정확히 확인하고 작성하셨습니까?"

        #time
        if sds_res['current_task'] == 'time':
            if sds_intent == 'again':
                talk_res.response.speech.utter = "통화 가능하신 요일과 시를 말씀해주세요"
            elif sds_intent == 'unknown':
                talk_res.response.speech.utter = "통화 가능하신 요일과 시를 말씀해주세요"
            elif sds_intent == "hourmiss":
                talk_res.response.speech.utter = "통화 가능 시를 말씀해주시지 않았습니다.\
                통화가능 시를 말씀해주세요."
            elif sds_intent == "daymiss":
                talk_res.response.speech.utter = "통화 가능 요일을 말씀해주시지 않았습니다.\
                통화가능 요일을 말씀해주세요."
            else:
                talk_res.response.speech.utter = "그럼 가능하신 시간을 알려주시면 다시 연락드리겠습니다,\
                편하신 요일과 시를, 말씀해주세요"

        #time_end       
        if sds_res['current_task'] == 'timeEnd':
            talk_res.response.speech.utter = "네 고객님, 말씀하신 시간에 다시 연락을 드리겠습니다,\
            현대해상 에이아이상담원 였습니다, 감사합니다. $callback$"
        if sds_res['current_task'] == 'taskEnd':
            #talk_res.response.speech.utter = "네 고객님, 소중한시간 내주셔서 감사합니다. 현대해상 고객센터였습니다. $complete$"
            talk_res.response.speech.utter = "소중한 시간 내주셔서 감사드립니다, 향후 불편하시거나 궁금하신점 있으시면, 담당자나 고객콜센터로 언제든지 연락주시기 바랍니다, 오늘도 행복한 하루 보내세요. $complete$"


        print("[ANSWER]: " + original_answer)
        #print("[SESSION_KEY] :" + )
        print("[ENGINE]: " + answer_engine)

        #위치 전송
        #self.DBConnect("update hc_hh_campaign_score set task='"+ sds_res['current_task'] + "' where contract_no = '" + seq + "';")


        return talk_res


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
