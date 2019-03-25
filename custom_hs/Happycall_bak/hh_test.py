#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re

reload(sys)
sys.setdefaultencoding('utf-8')

exe_path = os.path.realpath(sys.argv[0])
bin_path = os.path.dirname(exe_path)

lib_path = os.path.realpath(bin_path+"/../lib/python")
sys.path.append(lib_path)

# Basic lib import
from concurrent import futures
import argparse
import grpc
import time
from datetime import datetime


# pb import
from google.protobuf import empty_pb2
from google.protobuf import struct_pb2 as struct
from maum.m2u.da.v3 import talk_pb2
from maum.m2u.da.v3 import talk_pb2_grpc
from maum.m2u.da import provider_pb2
#from maum.m2u.server import pool_pb2
#from elsa.facade import userattr_pb2
from maum.m2u.facade import userattr_pb2


#import sds
#from maum.m2u.sds import sds_pb2
#from maum.m2u.facade import front_pb2

# Custom import
from qa.util import *
from qa.qa import QA
from qa import talk as dy
#from logger.logger import TLO
#from logger.logger import DA_LOG
#from logger.logger import KD_LOG
from logger.logger import * 
from custom.minds_gspread import GS
from custom.ngram_classifier import NgramClassifier

import phonemsg

__ONE_DAY_IN_SECONDS__ = 60 * 60 * 24

class DaMainServer(talk_pb2_grpc.DialogAgentProviderServicer):

    # STATE
    #state = provider_pb2.DIAG_STATE_IDLE
    init_param = provider_pb2.InitParameter()

    # PROVIDER
    provider = provider_pb2.DialogAgentProviderParam()
    provider.name = 'DA'
    provider.description = 'Hi, DA dialog agent'
    provider.version = '0.1'
    provider.single_turn = True
    provider.agent_kind = provider_pb2.AGENT_SDS
    provider.require_user_privacy = True
    #provider.user_privacy_attributes.extend(["location"])

    # SDS Stub
    sds_server_addr = ''
    sds_stub = None

    def __init__(self):
        self.state = provider_pb2.DIAG_STATE_IDLE
#        self.tlo_logger = TLO()
#        self.kd_logger = KD_LOG()
#        self.da_logger = DA_LOG()
        self.chat_logger = CHAT_LOG()

#        self.Sds = sds.SDS()
#        self.slots_name_list = []
#        self.slots_value_list = []
#        self.model = ''

    def IsReady(self, empty, context):
#        self.da_logger.write("is_ready called")
        status = provider_pb2.DialogAgentStatus()
        status.state = self.state
        return status

    def Init(self, init_param, context):
#        self.da_logger.write("initialize called")
        self.state = provider_pb2.DIAG_STATE_INITIALIZING
        # copy all
        self.init_param.CopyFrom(init_param)
        # direct method
        self.remote = init_param.params["remote"]
#        self.da_logger.write("remote")
        self.state = provider_pb2.DIAG_STATE_RUNNING
        # returns provider
        result = provider_pb2.DialogAgentProviderParam()
        result.CopyFrom(self.provider)
#        self.da_logger.write("result called")
        return result

    def Terminate(self, empty, context):
#        self.da_logger.write("terminate called")
        # do nothing
        self.state = provider_pb2.DIAG_STATE_TERMINATED
        return empty_pb2.Empty()

    def GetUserAttributes(self, empty, context):
#        self.da_logger.write("get_user_attributes called")
        result = userattr_pb2.UserAttributeList()
        return result

    def GetRuntimeParameters(self, empty, context):
        print ('GetRuntimeParameters', 'called')
        result = provider_pb2.RuntimeParameterList()
        return result

    def GetProviderParameter(self, empty, context):
#        self.da_logger.write("get_provider_parameter called")
        params = list()
        result = provider_pb2.RuntimeParameterList()
        remote = provider_pb2.RuntimeParameter()
        remote.name = "remote"
        remote.type = userattr_pb2.DATA_TYPE_STRING
        remote.desc = "remote"
        remote.default_value = ""
        remote.required = True
        params.append(remote)
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
        #logger.debug('Open request %s', request)
        print 'Open request: '+str(request)
        session_id = request.session.id
        #logger.debug('open_session_data %s %s', session_id, context)
        print 'open_session_data: '+ str(session_id)+', '+str(context)
        result = talk_pb2.TalkResponse()
        print 'OpenSkill end'
        return result


    def CloseSkill(self, request, context):
        #logger.debug('CloseSkill %s %s', request,context)

        result = talk_pb2.CloseSkillResponse()
        return result

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


    def Talk(self, talk, context):
        # Setting
        qna = dy.DA_Talk(question=talk.utter.utter)
        qna.session_id = talk.session.id    # SDS에 필요
        qna.model = 'Happy_Call_HH'           # SDS에 필요
        qna.skill_id = 7                    # BQA에 필요
        qna.com_id = 7                      # NGRAM에 필요

        # QA 진행 순서
        qna.call_bqa_exact()    # Exact Matching
        qna.call_ngram()        # NGRAM
        qna.call_bqa_1st()      # 1차검색
        qna.call_bqa_2nd()      # 2차검색
        qna.code_to_text()      # BQA CODE -> Text
        if qna.flag == False:
            qna.answer = self.get_unknown_msg()                 # Unknown 답변 넘겨주기
        qna.answer = self.ending_word(qna.answer, qna.engine)   # 답변 뒤에 '입니다.' 붙이기

        # 답변 설정
        original_answer = qna.answer                            # 챗봇 답변 받아와서 저장
        original_answer = self.filtering(qna.question, original_answer)           # 바보, 멍청이 등 입력 시 처리 
        output = original_answer.replace('\n', '$$NL$$').replace('\\n', '$$NL$$')   # 줄바꿈 변경
        talk_res = talk_pb2.TalkResponse()                      # talk_res 선언
        talk_res.response.speech.utter = output                 # 답변 저장
        qna.chat_log(chatbot=talk.chatbot, device=talk.system_context.device.id)    # CHAT_LOG (채팅 로그)
        talk_res.response.speech.utter += "$$HB_S$$위치,소개서,영상$$HB_F$$"        # 가로버튼 추가
        qna.print_result()                                      # 결과 콘솔 출력

        phoneto = '01084520997'
        phonefrom = '01084520997'
        phonetext = talk_res.response.speech.utter

        print ("문자메세지 발송 시작!")
        self.phonemsg = phonemsg.phonemsg()
        self.phonemsg.phonemsg(phoneto, phonefrom, phonetext)
        print("문자메세지 발송 완료!")

        return talk_res

    def filtering(self, question, answer):
        # 바보, 멍청이 등 입력 시 처리    
        word_list = ['바보', '멍청']
        for word in word_list:
            if word in question:
                main_uktext = ['정말 슬픈 말이네요. 제 대답에 만족하실 때까지 저도 열심히 공부할게요. 다른 질문은 없으신가요?',
                               '다음 번에 저랑 대화하실 땐 그런 생각이 들지 않도록 제가 진짜 열심히 공부할거예요! 다른 질문은 없으세요?']
                answer = random.choice(main_uktext)
                break;
        return answer

    def ending_word(self, txt, answer_engine):
        # 답변 엔진에 따라 답변 뒤에 '입니다.' 붙이기
        engines = ["KBQA", "EXO", "MRC"]
        txtEnd = ["다.", "요."]
        if answer_engine in engines and txt.strip()[-2:] not in txtEnd:
            txt = txt + "입니다."
        return txt

    def get_unknown_msg(self):
        # Return: Unknown Messange
        main_uktext = ['죄송해요, 제가 잘 못 알아 들었어요. ' + 
                         '아직 이렇게 모르는 게 있다니 저도 충격이네요…ㅠㅠ' +
                         '다음 번엔 꼭 대답할 수 있도록 열심히 공부할게요. ' + 
                         '다른 질문을 물어봐주시면, 그건 제가 꼭 대답해 볼게요!', 
                       '헛… 이건 제가 대답하기는 어려운 질문이네요. 저희 팀장님께 여쭤봐야 할 것 같은데….' +
                         '바로 해결해드리지 못해서 죄송해요. 다른 질문을 물어봐주시면, 그건 제가 꼭 대답해 드리겠어요!']
        return random.choice(main_uktext)
        

#    def passingTask(self, meta, original_answer, output, req_full_time, status_code, status_message, talk_res, answer_engine, engine_path):
#        talk_res.response.speech.utter = original_answer

        # temp code
#        talk_res.response.speech.utter = output

#        output = util.delete_space(output)
#        rsp_time = util.time_check()
#        meta = util.insert_meta(meta=meta, FROM_SVC_NAME="MFRT", TO_SVC_NAME="DA", RESULT_CODE=status_code, 
#                                REQ_TIME=req_full_time, RSP_TIME=rsp_time, LOG_TIME=rsp_time, QA_ENGINE='DA')
#        return talk_res

#    def runBasicQA(self, meta, question, skill_id, qa_type=0):
#        req_time = util.time_check()
#        output, original_answer, flag, status_code, status_message = qa.base_qa(text=question, meta=meta, skill_id=skill_id, qa_type=qa_type)
#        rsp_time = util.time_check()
#        meta = util.insert_meta(meta=meta, FROM_SVC_NAME="DA", TO_SVC_NAME="BASICQA", RESULT_CODE=status_code,REQ_TIME=req_time, RSP_TIME=rsp_time, LOG_TIME=rsp_time, QA_ENGINE=flag)
#        return flag, meta, original_answer, output, status_code, status_message

    def runKBQA(self, meta, question):
        req_time = util.time_check()
        print "func kbqa run"
        output, original_answer, flag, status_code, status_message = qa.kbqa(text=question, meta=meta)
        print "func kbqa end"
        rsp_time = util.time_check()
        meta = util.insert_meta(meta=meta, FROM_SVC_NAME="DA", TO_SVC_NAME="KBQA", RESULT_CODE=status_code,REQ_TIME=req_time, RSP_TIME=rsp_time, LOG_TIME=rsp_time, QA_ENGINE=flag)
        self.tlo_logger.write(meta=meta)
        return flag, meta, original_answer, output, status_code, status_message

    def runEXO(self, meta, question):
        req_time = util.time_check()
        output, original_answer, flag, status_code, status_message, weight, nlqa_result = qa.wise_qa(text=question,meta=meta)
        rsp_time = util.time_check()
        meta = util.insert_meta(meta=meta, FROM_SVC_NAME="DA", TO_SVC_NAME="EXOBRAIN", RESULT_CODE=status_code,REQ_TIME=req_time, RSP_TIME=rsp_time, LOG_TIME=rsp_time, QA_ENGINE=flag)
        self.tlo_logger.write(meta=meta)
        return flag, meta, nlqa_result, original_answer, output, status_code, status_message, weight

    def runMRC(self, meta, nlqa_result, question):
        req_time = util.time_check()
        output, original_answer, flag, status_code, status_message, weight, doc_weight, answer_weight, answer_doc = qa.mindsMRC(text=question,nlqa_result=nlqa_result)
        rsp_time = util.time_check()
        meta = util.insert_meta(meta=meta, FROM_SVC_NAME="DA", TO_SVC_NAME="MRC", RESULT_CODE=status_code,REQ_TIME=req_time, RSP_TIME=rsp_time, LOG_TIME=rsp_time, QA_ENGINE=flag)
        self.tlo_logger.write(meta=meta)
        return flag, meta, original_answer, output, status_code, status_message, weight, doc_weight, answer_weight, answer_doc

def serve():
    parser = argparse.ArgumentParser(description="DaMainServer DA")
    parser.add_argument("-p", "--port",
                        nargs="?",
                        dest="port",
                        required=True,
                        type=int,
                        help="port to access server")
    args = parser.parse_args()
    data = [
        ('grpc.max_connection_idle_ms', 10000),
        ('grpc.max_connection_age_ms', 10000)
    ]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), None, data, None)

    talk_pb2_grpc.add_DialogAgentProviderServicer_to_server(DaMainServer(), server)
    listen = "[::]" + ":" + str(args.port)
    server.add_insecure_port(listen)
    server.start()

    try:
        while True:
            time.sleep(__ONE_DAY_IN_SECONDS__)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    util = Util()
    qa = QA()
    gs = GS()
    serve()
