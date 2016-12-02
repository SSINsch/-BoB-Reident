# -*- coding: utf-8 -*-
import re
import Levenshtein
import csv
import statistics
from datetime import datetime

# 가정: database D는 aux A에 순서에 의해 정렬되어 있으며, 정돈되어 있음.
# 가정: 10대, 20대... 로 표시된 경우 '대'를 제거
# 가정: 각 Database 공통적인 정보만을 남기고 열을 삭제한다. 이 떄, 원본 DB는 남겨놔야 이후 매칭이 가능. (이는 개선가능성이 있다.)

class Reidentify1B(object):
    def __init__(self):
        database = []
        aux_array = []
        # open input files. f1=releasedD. f2=auxD
        f1 = open('./input_data/netflix_IMDB(Real).csv', 'r')
        f2 = open('./input_data/netflix_anony(Real).csv', 'r')
        self.readinput(f1, database)
        self.readinput(f2, aux_array)
        f1.close()
        f2.close()
        # score array = array for N by M
        score = [[1 for col in range(len(aux_array))] for row in range(len(database))]
        att_list = [dict() for row in range(len(database[0]))]
        metadata_list = []
        print('get metadata...')
        self.metadata_input(metadata_list)
        print("get weight...")
        self.weight(database, att_list)
        filter_list = [[0 for col in range(len(aux_array))] for row in range(len(database))]
        print("get score...")
        self.score(database, aux_array, att_list, score, filter_list, metadata_list)
        # matching set is the dictation array which will contain (candidate, possibility)
        matching = [dict() for row in range(len(database))]
        eccentricity = 0.00000001
        print("get matching...")
        self.matching_set(score, eccentricity, matching, filter_list)
        self.print_candidate_name(database, aux_array, matching)
        self.print_percentage_result(database, aux_array, matching)

    def matching_set(self, input_array, eccentricity, output_array, filter_list):
        for row in range(len(input_array)):
            maximum = max(input_array[row])
            temp = input_array[row][:]

            for i in range(5):
                try:
                    if filter_list[row][input_array[row].index(maximum)] != max(filter_list[row]):
                        pass
                    output_array[row][input_array[row].index(maximum)] = maximum
                    temp.remove(maximum)
                    maximum = max(temp)
                except:
                    continue
            """
            temp.remove(maximum)
            try:
                second_maximum = max(temp)
                deviation = statistics.stdev(input_array[row])
            except:
                second_maximum = 0
                deviation = 1
            if (maximum-second_maximum)/deviation >= eccentricity:
                output_array[row][input_array[row].index(maximum)] = maximum
            """

    def metadata_input(self, metadata_list):
        f = open('./metadata_input.txt', 'r')
        while True:
            line = f.readline()
            if not line:
                break
            metadata_list.append(line.lower())
        f.close()
        for i in range(len(metadata_list)):
            metadata_list[i] = metadata_list[i].replace('\n', '')

    def print_candidate_name(self, database, aux_array, matching):
        f = open('./result_candidate.txt', 'w')
        for row in range(len(database)):
            f.write(str(database[row])+'\n')
            for key in matching[row].keys():
                if matching[row][key] > 0:
                    f.write('=> ' + str(aux_array[key]) + ': ' + str(matching[row][key]) + '\n')
            f.write('\n')
        f.close()

    def print_percentage_result(self, database, aux_array, matching):
        f = open('./result_percentage.txt', 'w')
        f.write('CORRECT LIST\n')
        correct_num = 0
        targets = len(database)
        for row in range(targets):
            if database[row][0] == aux_array[max(matching[row], key=matching[row].get)][0]:
                f.write(str(database[row]) + '\n')
                correct_num += 1
        f.write('total: ' + str(targets) + '\n')
        f.write('correct: ' + str(correct_num) + '\n')
        f.write('percentage: ' + str((correct_num * 100) / targets) + '%')
        f.close()

    def readinput(self, file_handler, output_matrix):
        csv_reader = csv.reader(file_handler)
        iter_csv = iter(csv_reader)
        next(iter_csv)
        for row in csv_reader:
            output_matrix.append(row)

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

    def sim_string(self, aux, record):
        # case string: levenshtein distance
        error = Levenshtein.distance(str(record), str(aux))
        length = len(str(record)) if len(str(record)) > len(str(aux)) else len(str(aux))
        return 1 - (error / length)

    def sim_numrange(self, aux, record):
        # 속성값이 10,000~20,000 처럼 범위형으로 들어오고 , \과 같은 특수문자가 들어온다면 제거해준다.
        aux_pure = re.sub('[\$, ]', '', aux)
        record_pure = re.sub('[\$, ]', '', record)
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

    def score(self, database, aux_array, att_list, output, filter_list, metadata):
        for record in range(len(database)):
            for aux in range(len(aux_array)):
                res = 0
                for attribute in range(len(aux_array[aux])):
                    #temp = (1 - att_list[attribute][database[record][attribute]]) * self.sim_case(aux_array[aux][attribute], database[record][attribute], metadata[attribute])
                    temp = self.sim_case(aux_array[aux][attribute], database[record][attribute], metadata[attribute])
                    if temp > 0:
                        filter_list[record][aux] += 1
                    res += temp
                output[record][aux] = round(res, 4)

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
