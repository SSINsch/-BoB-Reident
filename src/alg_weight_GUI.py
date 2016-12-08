# coding: utf-8

import sys
import csv
import re
import Levenshtein
import statistics
from datetime import datetime
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class Reident(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.ui = uic.loadUi("../UI/de-anony_tools.ui")
        database = []
        aux_array = []
        att_list = []
        score = []
        matching = []
        filter_list = []
        metadata_list = []
        self.ui.Browse_anony.clicked.connect(lambda: self.fileOpen(database, self.ui.textBrowser_anony))
        self.ui.Browse_aux.clicked.connect(lambda: self.fileOpen(aux_array, self.ui.textBrowser_aux))
        self.ui.pushButton_weight.clicked.connect(lambda: self.getWeight(self.ui.textBrowser_result, database, att_list))
        self.ui.pushButton_run.clicked.connect(lambda: self.runFunction(self.ui.textBrowser_percentage, self.ui.textBrowser_result, database, aux_array,
                                                                        att_list, score, matching, filter_list, metadata_list))
        self.ui.pushButton_totrun.clicked.connect(lambda: self.totalrunFunction(self.ui.textBrowser_percentage, self.ui.textBrowser_result, database,
                                                                                aux_array, att_list, score, matching, filter_list, metadata_list))
        self.ui.pushButton_save.clicked.connect(lambda: self.testSave(self.ui.textBrowser_result))
        self.ui.actionAdd_metadata.triggered.connect(lambda: self.getMetadata(metadata_list, self.ui.textBrowser_result))
        self.ui.pushButton_quit.clicked.connect(self.closeEvent)
        self.ui.show()

    def printCorrectPercentage(self, textbrowser, database, aux_array, matching):
        textbrowser.clear()
        correct_num = 0
        targets = len(database)
        for row in range(targets):
            if database[row][0] == aux_array[max(matching[row], key=matching[row].get)][0]:
                correct_num += 1
            if database[row][0] != aux_array[max(matching[row], key=matching[row].get)][0]:
                textbrowser.append(str(database[row]))
        textbrowser.append('total: ' + str(targets))
        textbrowser.append('correct: ' + str(correct_num))
        textbrowser.append('percentage: ' + str((correct_num * 100) / targets) + '%')


    def getMetadata(self, metadata, textbrowser):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '../example', '(*.txt)')
        if fname[0]:
            metadata.clear()
            f = open(fname[0], 'r')
            while True:
                line = f.readline()
                if not line:
                    break
                metadata.append(line.lower())
            f.close()
            for i in range(len(metadata)):
                metadata[i] = metadata[i].replace('\n', '')
            textbrowser.append('metadata recorded...')

    def setFilterList(self, database, aux_array, output_matrix):
        for row in range(len(database)):
            output_matrix.append([])
            for col in range(len(aux_array)):
                output_matrix[row].append(0)

    def testSave(self, textBrowser_result):
        fname = QFileDialog.getSaveFileName(self, 'Save file')
        fhandle = open(fname[0], 'w')
        fhandle.write(textBrowser_result.toPlainText())
        fhandle.close()

    def totalrunFunction(self, textBrowser_percentage, textbrowser_result, database, aux_array, att_list, score_list, matching_list, filter, metadata):
        self.getWeight(textbrowser_result, database, att_list)
        self.runFunction(textBrowser_percentage, textbrowser_result, database, aux_array, att_list, score_list, matching_list, filter, metadata)

    def setMatchingSet(self, input_matrix, output_matrix):
        for row in range(len(input_matrix)):
            output_matrix.append(dict())

    def matchingSet(self, input_array, eccentricity, output_array):
        for row in range(len(input_array)):
            maximum = max(input_array[row])
            temp = input_array[row][:]

            temp.remove(maximum)
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

    def runFunction(self, textbrowser_percentage, textbrowser_result, database, aux_array, att_list, score_list, matching_list, filter, metadata):
        textbrowser_result.append("de-anonymization alg is running ...")
        if len(metadata) == 0:
            textbrowser_result.append("metadata error")
            return -1
        self.setScoreList(textbrowser_result, database, aux_array, score_list)
        self.setFilterList(database, aux_array, filter)
        self.getScore(database, aux_array, att_list, score_list, filter, metadata)
        textbrowser_result.append("done")
        self.setMatchingSet(database, matching_list)
        eccentricity = 0.00000001
        self.matchingSet(score_list, eccentricity, matching_list)
        self.printCandidate(textbrowser_result, database, aux_array, matching_list)
        self.printCorrectPercentage(textbrowser_percentage, database, aux_array, matching_list)

    def printCandidate(self, textbrowser_result, database, aux_array, matching):
        textbrowser_result.clear()
        for row in range(len(database)):
            textbrowser_result.append(str(database[row]))
            for key in matching[row].keys():
                textbrowser_result.append('=> ' + str(aux_array[key]) + ': ' + str(matching[row][key]))
            textbrowser_result.append('\n')

    def similarityCase(self, aux, record, metadata):
        if metadata == 'index':
            return 0
        elif metadata == 'string':
            return self.simString(aux, record)
        elif metadata == 'number_range':
            return self.simNumrange(aux, record)
        elif metadata == 'number':
            return self.simNum(aux, record)
        elif metadata == 'date':
            return self.simDate(aux, record)

    def simNum(self, aux, record):
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

    def simDate(self, aux, record):
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

    def simString(self, aux, record):
        # case string: levenshtein distance
        error = Levenshtein.distance(str(record), str(aux))
        length = len(str(record)) if len(str(record)) > len(str(aux)) else len(str(aux))
        return 1 - (error / length)

    def simNumrange(self, aux, record):
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
            aux_pure[1] = 1
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

    def getScore(self, database, aux_array, att_list, output_list, filter, metadata):
        progress_rate = 0
        len_database = len(database) / 100
        for record in range(len(database)):
            for aux in range(len(aux_array)):
                res = 0
                for attribute in range(len(aux_array[aux])):
                    temp = (1 - att_list[attribute][database[record][attribute]]) * self.similarityCase(
                        aux_array[aux][attribute], database[record][attribute], metadata[attribute])
                    if temp > 0:
                        filter[record][aux] += 1
                    res += temp
                output_list[record][aux] = round(res, 4)
            progress_rate += 1
            self.ui.progressBar.setValue(progress_rate / len_database)

    def setScoreList(self, textbrowser_result, database, aux_array, output_matrix):
        for row in range(len(database)):
            output_matrix.append([])
            for col in range(len(aux_array)):
                output_matrix[row].append(1)

    def getWeight(self, textbrowser_result, releaseD, att_list):
        textbrowser_result.append("weight calculating... \t")
        self.setAttList(textbrowser_result, releaseD, att_list)
        try:
            att_num = len(releaseD[0])
            record_num = len(releaseD)
        except:
            textbrowser_result.append("ERROR. should have to read input files...")
            return
        for att in range(att_num):
            dictkeys_list = list(att_list[att].keys())
            for record in range(record_num):
                if releaseD[record][att] not in dictkeys_list:
                    att_list[att][releaseD[record][att]] = 0
                    dictkeys_list.append(releaseD[record][att])
                att_list[att][releaseD[record][att]] += 1
            for num_dictkeys in range(len(dictkeys_list)):
                att_list[att][dictkeys_list[num_dictkeys]] /= record_num
        textbrowser_result.append("done")

    def setAttList(self, textbrowser_result, input_matrix, output_matrix):
        try:
            for row in range(len(input_matrix[0])):
                output_matrix.append(dict())
        except:
            textbrowser_result.append("ERROR. should have to read input files...")
            return

    def fileOpen(self, output_matrix, textbrowser):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '../input_data', '(*.csv)')
        if fname[0]:
            f = open(fname[0], 'r')
            with f:
                output_matrix.clear()
                csv_reader = csv.reader(f)
                iter_csv = iter(csv_reader)
                next(iter_csv)
                for row in csv_reader:
                    output_matrix.append(row)
            textbrowser.clear()
            textbrowser.append(fname[0])

    def closeEvent(self):
        reply = QMessageBox.question(self, 'message', "Are you sure to quit?",
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            app.quit()
        else:
            return



if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Reident()
    sys.exit(app.exec())
