# -*- coding: utf-8 -*-
import re
import Levenshtein
import csv
import statistics
from datetime import datetime

# 가정: database D는 aux A에 순서에 의해 정렬되어 있으며, 정돈되어 있음.
# 가정: 10대, 20대... 로 표시된 경우 '대'를 제거

class Reidentify1B(object):
    def __init__(self):
        # f1 = releasedD(database). f2 = auxD(aux_array)
        # score array = array for N(len_database) by M(len_aux_array)
        # att_list: 각 attribute의 비율을 가지는 dictionary의 list
        # metadata_list = array for metadata
        # filter_list = [[0 for col in range(len(aux_array))] for row in range(len(database))]
        # matching set is the dictation array which will contain (candidate, possibility)
        database = []
        aux_array = []
        f1 = open('../input_data/기본공통속성데이터/기본데이터(비식별화)(name_delete)_alive.csv', 'r')
        f2 = open('../input_data/기본공통속성데이터/기본데이터(원본).csv', 'r')
        self.readinput(f1, database)
        self.readinput(f2, aux_array)
        f1.close()
        f2.close()
        score = [[1 for col in range(len(aux_array))] for row in range(len(database))]
        att_list = [dict() for row in range(len(database[0]))]
        metadata_list = []
        print('get metadata...')
        self.metadata_input(metadata_list)
        print("get weight...")
        self.weight(database, att_list)
        filter_list = []
        print("get score...")
        self.score(database, aux_array, att_list, score, filter_list, metadata_list)
        matching = [dict() for row in range(len(database))]
        eccentricity = 0.00000001
        print("get matching...")
        self.matching_set(score, eccentricity, matching)
        self.print_candidate_name(database, aux_array, matching)
        self.print_percentage_result(database, aux_array, matching)

    # matching set을 구하는 함수.
    # input_array: 입력으로 들어오는 score 배열
    # eccentricity: 유의미한 차이 alpha
    # output_array: 출력, 즉 matching set 배열
    def matching_set(self, input_array, eccentricity, output_array):
        for row in range(len(input_array)):
            maximum = max(input_array[row])
            temp = input_array[row][:]
            temp.remove(maximum)
            # maximum 값과 second maximum 값을 구한다.
            while True:
                try:
                    second_maximum = max(temp)
                    if second_maximum == maximum:
                        temp.remove(second_maximum)
                    else:
                        deviation = statistics.stdev(input_array[row])
                        break
                except:
                    second_maximum = 0
                    deviation = 1
                    break
            # 그 후, maximum 값과 second maximum 값이 유의미한 차이를 보이고
            # 해당 maximum을 값으로 후보를 모두 matching set에 입력
            if (maximum - second_maximum) / deviation >= eccentricity:
                while True:
                    output_array[row][input_array[row].index(maximum)] = maximum
                    input_array[row].remove(maximum)
                    try:
                        maximum = max(input_array[row])
                        if maximum == second_maximum:
                            break
                    except:
                        break

    # metadata 입력 함수
    def metadata_input(self, metadata_list):
        f = open('../example/metadata_input.txt', 'r')
        while True:
            line = f.readline()
            if not line:
                break
            metadata_list.append(line.lower())
        f.close()
        for i in range(len(metadata_list)):
            metadata_list[i] = metadata_list[i].replace('\n', '')

    # 모든 매칭셋을 출력하는 함수
    def print_candidate_name(self, database, aux_array, matching):
        f = open('../result_candidate.txt', 'w')
        for row in range(len(database)):
            f.write(str(database[row])+'\n')
            for key in matching[row].keys():
                if matching[row][key] > 0:
                    f.write('=> ' + str(aux_array[key]) + ': ' + str(matching[row][key]) + '\n')
            f.write('\n')
        f.close()

    # 매칭셋을 토대로 맞춘 후보만을 출력하고 percentage를 계산
    # 이 때, 최고 유사율을 보이는 후보가 하나일때만 정답이라고 계산한다
    def print_percentage_result(self, database, aux_array, matching):
        f = open('../result_percentage.txt', 'w')
        f.write('CORRECT LIST\n')
        correct_num = 0
        targets = len(database)
        for row in range(targets):
            if database[row][0] == aux_array[max(matching[row], key=matching[row].get)][0]:
                temp = list(matching[row].values())
                len_list = len(temp)
                temp = list(set(temp))
                len_set = len(temp)
                if len_list == len_set:
                    correct_num += 1
                    f.write(str(database[row]) + '\n')
        f.write('total: ' + str(targets) + '\n')
        f.write('correct: ' + str(correct_num) + '\n')
        f.write('percentage: ' + str((correct_num * 100) / targets) + '%')
        f.close()

    # csv로부터 입력받는 함수
    def readinput(self, file_handler, output_matrix):
        csv_reader = csv.reader(file_handler)
        iter_csv = iter(csv_reader)
        next(iter_csv)
        for row in csv_reader:
            output_matrix.append(row)

    # 유사도 측정 케이스 함수. 입력된 metadata에 따라 연산이 달라진다.
    # aux: Aux 배열의 한 행
    # record: Database 배열의 한 행
    # metadata: metadata
    def sim_case(self, aux, record, metadata):
        if metadata == 'index':
            return 0
        elif metadata == 'string':
            return self.sim_string(aux, record)
        elif metadata == 'number_range':
            return self.sim_numrange(aux, record)
        elif metadata == 'number':
            return self.sim_num(aux, record)
        elif metadata == 'date':
            return self.sim_date(aux, record)

    # 단일 숫자 유사율 계산
    def sim_num(self, aux, record):
        try:
            aux_pure = int(aux)
        except:
            aux_pure = 0
        try:
            record_pure = int(record)
        except:
            record_pure = 0
        diff = abs(aux_pure - record_pure)
        if diff > record_pure:
            return 0
        return 1 - diff/record_pure

    # 날짜 데이터 유사율 계산
    def sim_date(self, aux, record):
        try:
            aux_date = datetime.strptime(aux, '%Y-%m-%d')
        except:
            aux_date = datetime.strptime('9999-12-31', '%Y-%m-%d')
        try:
            record_date = datetime.strptime(record, '%Y-%m-%d')
        except:
            record_date = datetime.strptime('9999-12-31', '%Y-%m-%d')
        delta = abs(aux_date - record_date)
        if delta.days == 0:
            return 1
        elif delta.days <= 7:
            return 0.5
        else:
            return 0

    # 문자열 유사율 계산. Levenshtein 알고리즘을 이용
    def sim_string(self, aux, record):
        # case string: levenshtein distance
        error = Levenshtein.distance(str(record), str(aux))
        length = len(str(record)) if len(str(record)) > len(str(aux)) else len(str(aux))
        return 1 - (error / length)

    # 범위형 숫자 유사율 계산
    def sim_numrange(self, aux, record):
        # 속성값이 10,000~20,000 처럼 범위형으로 들어오고 , \과 같은 특수문자가 들어온다면 제거해준다.
        aux_pure = re.sub('[\$\[,]', '', aux)
        record_pure = re.sub('[\$\[,]', '', record)
        # 10000~20000 등과 같을 때 1차원 배열 ( 10000 20000 ) 으로 문자를 치환 [~ => 띄어쓰기]
        aux_pure = re.sub('~', ' ', aux_pure)
        record_pure = re.sub('~', ' ', record_pure)
        # split by space
        aux_pure = aux_pure.split()
        record_pure = record_pure.split()

        if len(aux_pure) == 1:
            aux_pure.append(aux_pure[0])
        if len(record_pure) == 1:
            record_pure.append(record_pure[0])
        try:
            for i in range(len(aux_pure)):
                aux_pure[i] = float(aux_pure[i])
                aux_pure[i] = int(aux_pure[i])
        except:
            # 만일 동질집합처리 때문에 숫자가 아니라 '*'가 들어오면 의미없는 숫자[0, 1]로 대체
            aux_pure[0] = 0
            aux_pure[0] = 1
        try:
            for i in range(len(record_pure)):
                record_pure[i] = float(record_pure[i])
                record_pure[i] = int(record_pure[i])
        except:
            # 만일 동질집합처리 때문에 숫자가 아니라 '*'가 들어오면 의미없는 숫자[2, 3]로 대체. 단, aux와 겹치면 안 됌.
            record_pure[0] = 2
            record_pure[1] = 3

        # releaseD 의 범위 내에 aux 의 값이 포함되어있는지, 포함되어있다면 다음과 같이 유사도를 낸다.
        # 유사도 = (포함되는 수 개수 / 더 넓은 숫자범위)
        match = 0
        for i in range(record_pure[0], record_pure[1] + 1):
            if i in range(aux_pure[0], aux_pure[1] + 1):
                match += 1
        length = (record_pure[1] - record_pure[0] + 1) if (record_pure[1] - record_pure[0]) > (record_pure[1] - record_pure[0]) else (record_pure[1] - record_pure[0] + 1)
        return match / length

    # score를 계산하는 함수. 내부에서 sim_case 함수를 통해 케이스가 나누어진다.
    # database: 입력으로 들어오는 비식별 처리된 database
    # aux_array: 입력으로 들어오는 알려진 database (물론 또다른 비식별 처리된 database여도 된다.)
    # att_list: 각 attribute의 비율을 가지는 dictionary의 list
    # output: score 배열을 출력
    # filter_list: 필터링 배열. 이로써 일치하는 속성의 갯수가 최대갯수가 아니라면 해당 후보를 제외하는 효과가 있음
    # metadata: metadata
    def score(self, database, aux_array, att_list, output, filter_list, metadata):
        for record in range(len(database)):
            for aux in range(len(aux_array)):
                res = 0
                for attribute in range(len(metadata)):
                    temp = (1 - att_list[attribute][database[record][attribute]]) * self.sim_case(aux_array[aux][attribute], database[record][attribute], metadata[attribute])
                    # temp = self.sim_case(aux_array[aux][attribute], database[record][attribute], metadata[attribute])
                    if temp > 0:
                        filter_list[record][aux] += 1
                    res += temp
                output[record][aux] = round(res, 4)

    # 가중치 계산 함수.releaseD 내의 각 속성마다 값의 분포를 구하여 att_list에 저장한다.
    # releaseD: 입력으로 들어오는 비식별 처리된 database
    # att_list: 각 attribute의 비율을 가지는 dictionary의 list
    def weight(self, releaseD, att_list):
        att_num = len(releaseD[0])
        record_num = len(releaseD)
        for att in range(att_num):
            dictkeys_list = list(att_list[att].keys())
            for record in range(record_num):
                if releaseD[record][att] not in dictkeys_list:
                    att_list[att][releaseD[record][att]] = 0
                    dictkeys_list.append(releaseD[record][att])
                att_list[att][releaseD[record][att]] += 1
            for num_dictkeys in range(len(dictkeys_list)):
                att_list[att][dictkeys_list[num_dictkeys]] /= record_num


if __name__ == '__main__':
    temp = Reidentify1B()
