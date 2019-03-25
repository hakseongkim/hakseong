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
model = ''

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

        #session_id = talk.session.id
        print("talk : ", talk.utter.utter)
        seq = talk.utter.utter[talk.utter.utter.index("$callSeq")+9:-1]
        phoneNum = self.DBConnect("select phone from hc_hh_2_score where seq_num = '" + seq + "';")
        phoneNum = phoneNum[0]['phone']
        #phoneNum = '01034491702'
        uttertext = talk.utter.utter[talk.utter.utter.find(";$callSeq"):]
        talk.utter.utter = talk.utter.utter.replace(uttertext,"")


        dbsession = self.DBConnect("select session_name,phone,user_name,join_month,join_day,insurance_contractor,insurance_insured,insurance_closeproduct,privacy_add1,privacy_add2,insurance_productname from hc_hh_2_score where phone = '" + phoneNum + "';")
        # user_name 통화자(가입자)
        # join_month 가입 월
        # join_day 가입 일
        # insurance_contractor 가입 계약자
        # insurance_insured 가입 피보험자
        # insurance_closeproduct 무해지상품 s가입여부
        # privacy_add1 메인주소
        # privacy_add2 세부주소
        phone = dbsession[0]['phone']
        user_name = dbsession[0]['user_name']
        join_month = dbsession[0]['join_month']
        join_day = dbsession[0]['join_day']
        insurance_contractor = dbsession[0]['insurance_contractor']
        insurance_insured = dbsession[0]['insurance_insured']
        insurance_closeproduct = dbsession[0]['insurance_closeproduct']
        insurance_productname = dbsession[0]['insurance_productname']
        privacy_add1 = dbsession[0]['privacy_add1']
        privacy_add2 = dbsession[0]['privacy_add2']

        if dbsession[0]['session_name'] is None:
            dbsessioncode = talk.session.id
            self.DBConnect("update hc_hh_2_score set session_name = '" + str(dbsessioncode) + "' where phone = '" + phoneNum + "';")
            session_id = dbsessioncode
        else:
            session_id = int(dbsession[0]['session_name'])


        #print("talk.session.id : " + str(talk.session.id))
        #print("session.id : " + str(dbsession[0]['session_name']))
        #print("talk.session.id : " + talk.session.id + "---- talk.session.id type : " + type(talk.session.id))
        #print("session.id : " + dbsession[0]['session_name'] + "---- session.id type : " + type(dbsession[0]['session_name']))


        #print("dbsession : " + dbsession[0]['session_name'])

        #self.DBConnect("update test set session_name = '"+session_id+"' where phone = '01084520997';")
        #print ("session_id" + str(session_id))
        talk_res = talk_pb2.TalkResponse()
        #print ("session_id" + str(session_id))
        print ("talk : ", talk.utter.utter)
        # 참고 - task4 삭제,
        #개인정보 호출


        ##초기 모델 설정
        dbsession = self.DBConnect("select model from hc_hh_2_score where phone = '" + phoneNum + "';")
        if dbsession[0]['model'] is None:
            model = "Happy_Call_HH2"
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





        # SDS
        dbtask = self.DBConnect("select task from hc_hh_2_score where phone = '" + phoneNum + "';")
        task = dbtask[0]['task']
        if task == 'task3' and insurance_contractor == insurance_insured:
            sds_intent = self.Sds.GetIntent(talk.utter.utter, model)
            if sds_intent == 'affirm':
                talk.utter.utter = "$task5$"

        sds_intent = self.Sds.GetIntent(talk.utter.utter, model)
        if task == 'task2' and sds_intent == "affirm":
            print("성공11111")
            sds_res = self.Sds.Talk(talk.utter.utter, session_id, model)
            self.DBConnect("update hc_hh_2_score set model='privacy' where phone = '" + phoneNum + "';")
            model = 'privacy'

        #입력받는 주소를 여기다가 처리를 해줘야함
        if task == 'PRIVACY2' and sds_intent == "affirm":
            print("성공22222")
            talk.utter.utter = '$next$'
            self.DBConnect("update hc_hh_2_score set model='Happy_Call_HH2' where phone = '" + phoneNum + "';")
            model = 'Happy_Call_HH2'
        if task == 'PRIVACY2' and sds_intent == "negate":
            print("성공22222")
            talk.utter.utter = '$next2$'
            self.DBConnect("update hc_hh_2_score set model='Timesetting' where phone = '" + phoneNum + "';")
            model = 'Happy_Call_HH2'
        if task == 'PRIVACY3' and sds_intent == "privacy3":
            print("성공333333")
            self.DBConnect("update hc_hh_2_score set model='Happy_Call_HH2' where phone = '" + phoneNum + "';")
            model = 'Happy_Call_HH2'


        sds_res = self.Sds.Talk(talk.utter.utter, session_id, model)
        #self.DBConnect("update test set task='" + sds_res['current_task'] + "' where phone = '" + phoneNum + "';")
        #sds_intent = self.Sds.GetIntent(talk.utter.utter, model)


        # 결과값 DB에 저장하는 방식
        b = []
        for i in range(1, 6):
            b.append("task" + str(i))
        for i in range(1, 4):
            b.append("PRIVACY" + str(i))



        if task in b:
            if sds_intent == 'affirm':
                self.DBConnect("update hc_hh_2_score set " + task + "='네' where phone = '" + phoneNum + "';")
            elif sds_intent == 'negate':
                self.DBConnect("update hc_hh_2_score set " + task + "='아니오' where phone = '" + phoneNum + "';")
            elif sds_intent == 'next':
                pass
            else:
                self.DBConnect("update hc_hh_2_score set " + task + "='"+talk.utter.utter+"' where phone = '" + phoneNum + "';")

        if task is not None or sds_intent != 'next':
            self.DBConnect("insert into hc_hh_2_result (phone, user_name, session_name, model, task, utter, intent, request_time) values('" + str(phone) + "','" + user_name + "','" + str(session_id) + "','" + model + "','" + str(task) + "','" + talk.utter.utter + "','" + sds_intent + "',NOW());")



        print("SDS Start!")
        #dbtask = self.DBConnect("select task from test where phone = '" + phoneNum + "';")
        #task = dbtask[0]['task']

        #print("++++++++++++++++taskname : " + sds_res['current_task'] + "intent : " + dialog_act)


        print(sds_res)
        #print("===============test=============")

        original_answer = sds_res['response']
        answer_engine = "SDS"
        engine_path.append("SDS")

        #original_answer = self.unknown_answer()
        #첫 SDS 답변 입력사항
        original_answer = sds_res['response']
        talk_res.response.speech.utter = original_answer

        #시간 컨펌
        if sds_res['current_task'] == 'timeAffirm':
            items = sds_res['intent.filled_slots.items']
            #print(items)
            for id in items:
                a[id[0]] = id[1]
                print(id)
            #text_nextweek = a['nextweek']
            #다음주의 기능까지 만들어서 넣어야 할까?
            text_day = a['day']
            text_part = a['part']
            text_hour = self.readNumberHour((a['hour']))
            #text_output = self.readNumber(31)
            #talk_res.response.speech.utter = text_output
            talk_res.response.speech.utter = "말씀하신 시각이 " + text_day +" "+ text_part + " "+ text_hour + "시가 맞습니까?"
            #말씀하신 일정이 11월 19일 오전 3시 30분이 맞습니까?

           # if text_nextweek is None:
           #     if text_day is None:
           #         if text_hour is None:
           #             talk_res.response.speech.utter = "원하시는 시간을 말씀해주세요"
           #         if text_part is None:
           #             pass

        #질문 수정사항
        sds_intent = self.Sds.GetIntent(talk.utter.utter, model)
        #task1
        if sds_res['current_task'] == 'task1':
            talk_res.response.speech.utter = "안녕하십니까?, 현대해상, 홍길동 입니다, " + user_name + " 고객님 되십니까?"
        #task2
        if sds_res['current_task'] == 'task2':
            talk_res.response.speech.utter = "지난" + self.readNumberMinite(join_month) + "월," + self.readNumberMinite(join_day) +"일 저희 현대해상에 "+insurance_productname+"을 가입해 주셔서, 진심으로 감사드립니다, 가입하신 계약이 정확하게 체결 되었는지, 안내 해드리고자 하는데요, 잠시 통화 가능하십니까?"
        #PRIVACY2
        if sds_res['current_task'] == 'PRIVACY2':
            talk_res.response.speech.utter = "고객님의 주소는 " + privacy_add1 + ", " + privacy_add2 + "로 확인 되는데 맞으십니까?"
        #PRIVACY3
        if sds_res['current_task'] == 'PRIVACY3':
            talk_res.response.speech.utter = "고객님의 주소는 " + privacy_add1 + " 으로 확인되는데요, 나머지 주소는 어떻게 되십니까?"
        # task3
        if sds_res['current_task'] == 'task3':
            talk_res.response.speech.utter = "확인 감사드립니다, 게약자와 피보험자가 다른 계약의 경우에는, 피보험자이신 "+insurance_insured+"님의 계약체결에 대한 동의가 반드시 필요합니다. 자필서명이 정확하게 이루어지지 않은 경우 무효계약으로 고객님꼐서 불이익을 보실 수 있습니다. 피보험자이신 고객님께서 청약서에 직접 자필서명을 하셨는지요?"

        print("[ANSWER]: " + original_answer)
        #print("[SESSION_KEY] :" + )
        print("[ENGINE]: " + answer_engine)

        #위치 전송
        self.DBConnect("update hc_hh_2_score set task='"+ sds_res['current_task'] + "' where phone = '" + phoneNum + "';")


        return talk_res

    # 1~999
    def readNumberMinite(self,n):


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
        return ''.join(result[::-1])


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
