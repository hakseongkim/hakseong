#!/usr/bin/python
# -*- coding: utf-8 -*-

###
# 프로그램명 : SDS Module
# 작성자 : 최현종
# 검수자 : 유재국
# 최초 작성일 : 2018-01-05
# 프로그램 목적 : SDS 시나리오 대화 모델에서 답변 호출
###

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import grpc
from google.protobuf import empty_pb2
from google.protobuf import json_format
import os
import time
import traceback

# Path
exe_path = os.path.realpath(sys.argv[0])
bin_path = os.path.dirname(exe_path)
lib_path = os.path.realpath(bin_path + '/../lib/python')
sys.path.append(lib_path)

from maum.brain.sds import sds_pb2
from maum.brain.sds import sds_pb2_grpc
from maum.brain.sds import resolver_pb2
from maum.brain.sds import resolver_pb2_grpc


class SDS:
    ### SDS 서버 실행
    # 해당 Model은 maum/trained/sds-model/ke/ 안에 위치
    def GetSdsServer(self, model):
        model_list = [model]

        sds_channel = grpc.insecure_channel('0.0.0.0:9860')
        resolver_stub = resolver_pb2_grpc.SdsServiceResolverStub(sds_channel)
        # Model Group
        MG = resolver_pb2.ModelGroup()
        MG.name = model
        MG.lang = 0
        MG.is_external = True
        #resolver_stub.CreateModelGroup(MG)
        try:
            resolver_stub.CreateModelGroup(MG)
        except Exception as e:
            print(e)
            traceback.print_exc(limit=None) 
        Model = resolver_pb2.Model()
        Model.lang = MG.lang
        Model.is_external = MG.is_external

        MP = resolver_pb2.ModelParam()
        MP.lang = MG.lang
        MP.is_external = MG.is_external
        MP.group_name = MG.name

        ML = resolver_pb2.ModelList()

        for mn in model_list:
            Model.name = mn
            MP.model_name = mn
            Model = ML.models.add()
            resolver_stub.LinkModel(MP)

        server_status = resolver_stub.Find(MG)
        print "<Find result>"

        # 서버가 시동중일 때 sleep 필요
        if server_status.state is resolver_pb2.SERVER_STATE_STARTING:
            print "SERVER STARTING"
            time.sleep(0.5)

        self.sds_stub = sds_pb2_grpc.SpokenDialogServiceStub(grpc.insecure_channel(server_status.server_address))
#        self.sds_stub = sds_pb2_grpc.SpokenDialogServiceInternalStub(grpc.insecure_channel(server_status.server_address))


        self.sds_server_addr = server_status.server_address

    ### SDS 시나리오 대화 모델에서 답변 호출
    def Talk(self, input_text, session_id, model, indri_score=0):
        self.GetSdsServer(model)

        empty = empty_pb2.Empty()
        cML = self.sds_stub.GetCurrentModels(empty)
        aML = self.sds_stub.GetAvailableModels(empty)
        dp = sds_pb2.DialogueParam()
        dp.model = model


        dp.session_key = session_id
        dp.user_initiative = True
        print("-----------------------------------------")
        print("[type]: %s" % (type(dp)))
        print("[dp]: %s" % (dp))
        print("-----------------------------------------")

        OpenResult = self.sds_stub.Open(dp)
        print("-----------------------------------------")
        print("[type]: %s" % (type(OpenResult)))
        print("[dp]: %s" % (OpenResult))
        print("-----------------------------------------")

        print("test1")
        sq = sds_pb2.SdsQuery()
        sq.model = dp.model
        sq.session_key = dp.session_key
        print("test2")
#        sq.apply_indri_score = indri_score
        print("test3")
        sq.utter = input_text

        print("test4")
        intent = self.sds_stub.Understand(sq)
        entities = sds_pb2.Entities()
        entities.session_key = dp.session_key
        entities.model = dp.model
        print '<intent>', intent
        sds_utter = self.sds_stub.Generate(entities)
        print(sds_utter)
        print '<intent.slu>', intent.origin_best_slu
        print '<intent.intent>', intent.intent
        print '<intent.filled_entities>', intent.filled_entities

        print '<intent.filled_slots.items()>', intent.filled_entities.items()
        confidence = sds_utter.confidence

        skill = json_format.MessageToDict(intent).get('filledEntities')
        if skill:
            skill = skill.get('skill')
        if sds_utter.finished == True:
            self.sds_stub.Close(dp)
        #return sds_utter.response.replace('\n', '')
        return {"response":sds_utter.response.replace('\n', ''),
                "intent":sds_utter.system_intent, "confidence":confidence,
                "best_slu":intent.origin_best_slu,
                "slots":intent.filled_entities,
                "skill":skill,
                "intent.filled_slots.items":intent.filled_entities.items()}

    def CloseTalk(self, session_id, skill):
        dp = sds_pb2.DialogueParam()
        dp.model = skill
        dp.session_key = session_id
        dp.user_initiative = True
        try:
            self.sds_stub.Close(dp)
            print "Talk Closed"
        except:
            print "Talk Close:Fail"


if __name__ == '__main__':
    print "If you want to Exit, Please type 'Ctrl+C'"
    try:
        while True:
            sds_model_path = '/srv/maum/trained/sds-model/ke/'
            file_list = os.listdir(sds_model_path)
            file_list.sort()

            print "\nSelect Model Number!\n"
            for i in range(len(file_list)):
                print str(i+1) + '.', file_list[i]

            number = raw_input("\nModel Number: ")
            model = file_list[int(number)-1]

            SDS = SDS()

            print "\nLet's Talk!\n"
            while True:

                question = raw_input("Question : ")
                answer = SDS.Talk(str(question), 1, model)
                print "answer: {} ({}) ({}) ({})".format(
                    answer['response'], answer['intent'],
                    answer['confidence'], answer['skill'])

    except KeyboardInterrupt:
        print "\nExit"
