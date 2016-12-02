# -*- coding: utf-8 -*-
import re
import Levenshtein
import csv

# 가정: database D는 aux A에 순서에 의해 정렬되어 있으며, 정돈되어 있음.
# 가정: 10대, 20대... 로 표시된 경우 '대'를 제거
# 가정: 문자열에는 '~'가 없어야 한다. (있어도 되지만 결과의 정확도가 조금 떨어질 수 있음.)
# 가정: 각 Database 공통적인 정보만을 남기고 열을 삭제한다. 이 떄, 원본 DB는 남겨놔야 이후 매칭이 가능. (이는 개선가능성이 있다.)

class Reidentify(object):
    def __init__(self):
        database = []
        aux_array = []
        # open input files. f1=releasedD. f2=auxD
        f1 = open('./넷플릭스(Real).csv', 'r')
        f2 = open('./IMDB(Real).csv', 'r')
        self.readinput(f1, database)
        self.readinput(f2, aux_array)
        f1.close()
        f2.close()
        # score array = array for N by M
        score = [[1 for col in range(len(aux_array))] for row in range(len(database))]
        self.score(database, aux_array, score)
        alpha = 0.1
        # matching set is the dictation array which will contain (candidate, possibility)
        matching = [dict() for row in range(len(database))]
        self.matching_set(score, alpha, matching)
        self.print_candidate_name(database, aux_array, matching)

    # print the candidate
    def print_candidate_name(self, database, aux_array, matching):
        f = open('./result.txt', 'w')
        for row in range(len(database)):
            f.write(str(database[row])+'\n')
            for key in matching[row].keys():
                f.write('=> ' + str(aux_array[key]) + ': ' + str(matching[row][key]) + '\n')
            f.write('\n')
        f.close()

    def readinput(self, file_handler, output_matrix):
        csv_reader = csv.reader(file_handler)
        iter_csv = iter(csv_reader)
        next(iter_csv)
        for row in csv_reader:
            output_matrix.append(row)

    def sim(self, aux, record):
        # 속성값이 10,000~20,000 처럼 범위형으로 들어오고 , \과 같은 특수문자가 들어온다면 제거해준다.
        aux_pure = re.sub('[\$, ]', '', aux)
        record_pure = re.sub('[\$, ]', '', record)
        # 10000~20000 등과 같을 때 1차원 배열 ( 10000 20000 ) 으로 문자를 치환 [~ => 띄어쓰기]
        aux_pure = re.sub('~', ' ', aux_pure)
        record_pure = re.sub('~', ' ', record_pure)
        # split by space
        aux_pure = aux_pure.split()
        record_pure = record_pure.split()
        # 애초에 space가 없었다면 배열은 원소를 하나만을 가진다. 이를 체크해서 원소가 두개이도록 모두 바꾼다.
        # (1) 입력이 (10~20)으로 들어왔다면 split 단계 이후에는 (10,20)과 같은 원소 2개의 배열 형태
        # (2) 입력이 애초에 (10~20)으로 들어온게 아니라 (10)과 같이 숫자 하나로 들어왔다면, split 단계까지 진행되었을 때 원소를 (10)만 가지게 된다.
        # 입력 인자에 통일성을 주기 위해 (2)번과 같은 경우에는 (10) => (10,10)으로 변경해준다.
        if len(aux_pure) == 1:
            aux_pure.append(aux_pure[0])
        if len(record_pure) == 1:
            record_pure.append(record_pure[0])

        # 배열의 원소가 숫자라면 이를 숫자로 인식하도록 int 함수를 적용.
        # 만일 두 비교대상 중 하나라도 숫자가 아니라면 문자열 vs 문자열로 비교해야하므로 is_string이라는 flag로 문자열인지 체크를 해준다.
        # 하나라도 문자열이라면 밑에 case string 을 수행하고 return
        # 모두 숫자라면 case number 를 수행
        is_string = 0
        try:
            for i in range(len(aux_pure)):
                aux_pure[i] = int(aux_pure[i])
        except ValueError:
            is_string = 1
        try:
            for i in range(len(record_pure)):
                record_pure[i] = int(record_pure[i])
        except ValueError:
            is_string = 1

        # case string
        # 어느 하나라도 string 이라면 Levenshtein algorithm 을 수행한다.
        # 유사도 = 1 - (다른 문자 갯수 / 긴 문자열의 길이)
        if is_string == 1:
            error = Levenshtein.distance(str(record_pure[0]), str(aux_pure[0]))
            length = len(str(record_pure[0])) if len(str(record_pure[0])) > len(str(aux_pure[0])) else len(str(aux_pure[0]))
            return 1 - (error / length)

        # case number
        # releaseD 의 범위 내에 aux 의 값이 포함되어있는지, 포함되어있다면 다음과 같이 유사도를 낸다.
        # 유사도 = (포함되는 수 개수 / 더 넓은 숫자범위)
        match = 0
        for i in range(record_pure[0], record_pure[1] + 1):
            if i in range(aux_pure[0], aux_pure[1] + 1):
                match += 1
        length = (record_pure[1] - record_pure[0] + 1) if (record_pure[1] - record_pure[0]) > (record_pure[1] - record_pure[0]) else (record_pure[1] - record_pure[0] + 1)
        return match / length

    def score(self, database, aux_array, output):
        f = open('./output.txt', 'w')
        f2 = open('./output2.txt', 'w')
        for record in range(len(database)):
            for aux in range(len(aux_array)):
                minimum = 1
                for attribute in range(len(aux_array[aux])):
                    res = self.sim(aux_array[aux][attribute], database[record][attribute])
                    if minimum > res:
                        output[record][aux] = round(res, 4)
                        minimum = round(res, 4)
                # f.writelines(str(database[record]))
                # f.writelines(str(aux_array[aux]))
                # f.writelines(str(output[record]))
            f2.write(str(record + 1) + ': ' + str(database[record]) + '\n')
            f2.write(str(output[record]) + '\n')
        f.close()
        f2.close()

    def matching_set(self, input_array, alpha, output_array):
        for row in range(len(input_array)):
            for col in range(len(input_array[row])):
                if input_array[row][col] >= alpha:
                    output_array[row][col] = input_array[row][col]
            # print(row, output_array[row])

    def setting_alpha(self):
        pass


if __name__ == '__main__':
    re = Reidentify()