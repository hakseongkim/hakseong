#!/usr/bin/python
# -*- coding: utf-8 -*-

###
# 프로그램명 : SDS Module
# 작성자 : 최현종
# 검수자 : 유재국
# 최초 작성일 : 2018-01-05
# 프로그램 목적 : SDS 시나리오 대화 모델에서 답변 호출
###

#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')
#import grpc
#from google.protobuf import empty_pb2
#from google.protobuf import json_format
#import os
#import time
#import traceback
import re
import datetime
import pymysql
import time
from google.protobuf import empty_pb2
from google.protobuf import struct_pb2 as struct
from google.protobuf.json_format import MessageToJson
import json
#
## Path
#exe_path = os.path.realpath(sys.argv[0])
#bin_path = os.path.dirname(exe_path)
#lib_path = os.path.realpath(bin_path + '/../lib/python')
#sys.path.append(lib_path)
#
#from maum.brain.sds import sds_pb2
#from maum.brain.sds import sds_pb2_grpc
#from maum.brain.sds import resolver_pb2
#from maum.brain.sds import resolver_pb2_grpc


class FUNC:

################################################## 시간을 잡아 주는 로직 ########################


    def convert_time(self, var):
        global convart_var
        hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', var.decode('utf-8')))
        print(hanCount)
        if hanCount >= 1:
            print("한글 확인")
            convart_var = self.change_bu(var.decode('utf-8'))
            print('convart_var : ' + convart_var)
            hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', convart_var.decode('utf-8')))
            print(hanCount)
            if hanCount >= 1:
                convart_ver = self.change(convart_var.decode('utf-8'))
            else:
                print('1차의 한글 더이상 없음1')
                pass
        else:
            print('2차의 한글 더이상 없음2')

        return convart_var


################################################### 한글로 변환시키는 로직(하나 둘 셋) #########################



#    def readNumberCount(self,n):
#        result = ''
#        nums = '영,일,이,삼,사,오,육,칠,팔,구'.split(',')
#        for i in list(n):
#            #print(i)
#            result = result + str(nums[int(i)])
#
#        return result
#    
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
                        tmpResult = tmpResult + num * dic[token.encode('utf-8')]
                    else:
                        tmpResult = tmpResult + 1 * dic[token.encode('utf-8')]

                else:
                    tmpResult = tmpResult + num
                    if tmpResult != 0:
                        result = result + tmpResult * dic[token.encode('utf-8')]
                    else:
                        result = result + 1 * dic[token.encode('utf-8')]
                    tmpResult = 0

                num = 0
            else:
                num = check
        return result + tmpResult + num

#########################################슬롯 값에 따라서 일정을 변화하는 로직 설정###############
    def next_call_schedule(self, slot_nextweek, slot_morae, slot_input_month, slot_input_day,\
    slot_tomorrow, slot_today, slot_day, slot_part,slot_hour, slot_minute):

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

        next_month = ""
        next_day = ""
        next_part = ""
        next_hour = ""
        next_minute = ""
        next_time = datetime.datetime.now()


        print ("input_nextweek : " + str(slot_nextweek))
        print ("input_morae : " + str(slot_morae))
        print ("input_tomorrow : " + str(slot_tomorrow))
        print ("input_today : " + str(slot_today))
        print ("input_day : " + str(slot_day))
        print ("input_part : " + str(slot_part))
        print ("input_hour : " + str(slot_hour))
        print ("input_minute : " + str(slot_minute))
        print("시이이이이이작")
        if slot_input_month is not None and slot_input_month != "":
            if slot_input_day is not None and slot_input_day != "":
                print ("일월 입력")
                next_time = next_time.replace(month=int(slot_input_month), day=int(slot_input_day))
            elif slot_input_day is None and slot_input_day == "":
                print ("월은 있는데 일은 입력되지 않았습니다.")
                if slot_morae == "모레" or slot_morae == "내일 모레" or slot_morae == "내일모레":
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
                #elif slot_nextweek == "" or slot_nextweek is None:
                #    pass
                else:
                #    talk.utter.utter = "$inputMiss$"
                    talk.utter.utter = "$dayMiss$"
        elif slot_input_month is None or slot_input_month == "":
            if slot_input_day is not None and slot_input_day != "":
                #next_time = next_time.replace(day=int(slot_input_day))
                if slot_morae == "모레" or slot_morae == "내일 모레" or slot_morae == "내일모레":
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
                     talk.utter.utter = "$dayMiss$"
                
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
                next_time = next_time.replace(hour=int(next_time.hour), minute=int(next_time.minute))
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
        
        now_time = datetime.datetime.now()
        try:
            if slot_part == '오후':
                next_time = next_time.replace(hour=next_time.hour + 12)

            
            if next_day == now_time.day:
                if next_time.hour <= now_time.hour:
                    next_day = int(next_day) + 7
                    next_time = next_time.replace(day=next_time.day + 7)
                    print(next_time)
            else:
                pass
        except:
            pass

        if slot_part == "오전" or slot_part == "오후":
            next_part = slot_part
            print("나와ㄸ따다ㅣㅏㅓ아러나리어나리어나리어내ㅏ")
            #talk.utter.utter = "$hourMiss$"
            next_hour = next_time.hour
            if next_time.hour > 12 and next_time.hour < 24:
            #   next_part = "오후"
                next_hour = next_time.hour - 12
            elif next_time.hour == 12:
                next_hour = 12
            elif next_time.hour > 0 and next_time.hour < 12:
                #  next_part = "오전"
                next_hour = next_time.hour
            elif next_time.hour == 0:
                pass
            #next_time.minute = ""
                
        else:
            if next_time.hour >= 1 and next_time.hour < 9:
                next_part = "오후"
                next_hour = next_time.hour

            elif next_time.hour >= 13 and next_time.hour <= 24:
                next_part = "오후"
                next_hour = next_time.hour - 12
            elif next_time.hour == 12:
                next_part = "오후"
                next_hour = 12
            elif next_time.hour >= 9 and next_time.hour < 12:
                next_part = "오전"
                next_hour = next_time.hour
            elif next_time.hour == 0:
                next_part = "오전"
                next_hour = next_time.hour
           # print(str(inext_time))
           #  next_hour = int(next_time.hour)

        next_minute = next_time.minute
        #slot_hour = self.readNumberHour((a['hour']))
        #text_output = self.readNumber(31)
        #talk_res.response.speech.utter = text_output
        print(next_time)
        return (next_time, next_month, next_day, next_part, next_hour, next_minute)


    ####################################### 세션 값 초기 설정 ##################
#    def input_session(self):
#        logic_count = json.dumps(
#            [
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
#            ]
#        )
#
#        session_data = struct.Struct()
#
#        return session_data, logic_count
#    ######################################### 세션 값 업데이트 ##################
#    def update_session(self, task, value, session_context, session_id):
#        dic = dict(session_context)
#        count_dic = json.loads(dic.get('count'))
#        count_dic[0][task] = value
#        session_data = struct.Struct()
#        session_data['id'] = session_id
#        session_data['count'] = count_dic
##        talk_res.response.session_update.context.CopyFrom(session_data)
#
#        return session_data
#
#
#    ######################################### 세션 값 추출  #####################
#    def get_session(self, task, session_context):
#        dic = json.loads(MessageToJson(session_context))
#        count_dic = dic.get('count')[0].get(task)
#
#        return count_dic
    


