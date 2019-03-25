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
model = 'ediya_kiosk'

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


#    def DBConnect(self, query):
#        conn = pymysql.connect(user="aicc",
#                               password="ggoggoma",
#                               host="aicc-bqa.cjw9kegbaf8s.ap-northeast-2.rds.amazonaws.com",
#                               database="happycall",
#                               charset="utf8",
#                               use_unicode=False)
#        curs = conn.cursor(pymysql.cursors.DictCursor)
#        #query = "select * from test;"
#        print(query)
#        curs.execute(query)
#        print("query good!")
#        rows = curs.fetchall()
#
#        print(rows)
#        curs.execute("commit;")
#        curs.close()
#        conn.close()
#        return rows


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
        print("talk : ", talk.utter.utter)
        session_id = talk.session.id
        
        model = "ediya_kiosk"

#        meta = dict()
#        #meta['seq_id'] = util.time_check(0)
#        meta['log_type'] = 'SVC'
#        meta['svc_name'] = 'DA'
#
#        #output = ""
#        original_answer = ""
#        engine_path = list()
#        answer_engine = "None"
#        status_code = ""
#        status_message = ""
#        flag = False
#        weight = 0
#        code = 'None'
        sds_intent = ""
        sds_res = self.Sds.Talk(talk.utter.utter, session_id, model)

        #sds_intent = self.Sds.GetIntent(talk.utter.utter, model)
        #print("sds_intent의 값 : " + str(sds_intent))

        #if sds_intent == 'overlap' or sds_intent == 'noproportion':

        print("SDS Start!")
            #talk.utter.utter = "$task4$"
        print(sds_res)
        #print("===============test=============")

        original_answer = sds_res['response']
        #answer_engine = "SDS"
        #engine_path.append("SDS")

        #original_answer = self.unknown_answer()
        #첫 SDS 답변 입력사항
        #talk_res.response.speech.utter = original_answer

#        if sds_res['current_task'] == 'timeAffirm':
#            items = sds_res['intent.filled_slots.items']
#            print(items)
#            for id in items:
#                a[id[0]] = id[1]
#                print(id)
#            if a['nextweek'] == "" : slot_nextweek = ""
#            elif a['nextweek'] == '돌아오는' : slot_nextweek = "다음" 
#            else: slot_nextweek = a['nextweek']
#            if a['morae'] == "" : slot_morae = ""
#            else: slot_morae = a['morae']
#            if a['input_month'] == "" : slot_input_month = ""
#            else: slot_input_month = a['input_month']
#            if a['input_day'] == "" : slot_input_day = ""
#            else: slot_input_day = a['input_day']
#            if a['tomorrow'] == "" : slot_tomorrow = ""
#            else: slot_tomorrow = a['tomorrow']
#            if a['today'] == "" : slot_today = ""
#            else: slot_today = a['today']
#            if a['day'] == "" : slot_day = ""
#            else: slot_day = a['day']
#            if a['part'] == "" : slot_part = ""
#            elif a['part'] == '저녁' or  a['part'] == '밤': slot_part = "오후" 
#            elif a['part'] == '아침' or  a['part'] == '새벽': slot_part = "오전" 
#            else: slot_part = a['part']
#            if a['hour'] == "" : slot_hour = ""
#            else: slot_hour = a['hour']
#            if a['minute'] == "" : slot_minute = ""
#            elif a['minute'] == "반": slot_minute = "30"
#            else: slot_minute = a['minute']
            #next_minute = ""
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


        #print("[ANSWER]: " + original_answer)
        #print("[SESSION_KEY] :" + )
        #print("[ENGINE]: " + answer_engine)

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
    def change_bu(input):
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
    def change(input):
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
