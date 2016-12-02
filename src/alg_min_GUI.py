# coding: utf-8

import sys
import csv
import re
import Levenshtein
from datetime import datetime
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class Reident(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.ui = uic.loadUi("de-anony_tools_new.ui")
        database = []
        aux_array = []
        att_list = []
        score = []
        matching = []
        self.ui.Browse_anony.clicked.connect(lambda: self.fileOpen(database, self.ui.textBrowser_anony))
        self.ui.Browse_aux.clicked.connect(lambda: self.fileOpen(aux_array, self.ui.textBrowser_aux))
        self.ui.pushButton_run.clicked.connect(lambda: self.runFunction(self.ui.textBrowser_percentage, self.ui.textBrowser_result, database, aux_array,
                                                                        att_list, score, matching))
        self.ui.pushButton_totrun.clicked.connect(lambda: self.totalrunFunction(self.ui.textBrowser_percentage, self.ui.textBrowser_result, database,
                                                                                aux_array, att_list, score, matching))
        self.ui.pushButton_save.clicked.connect(lambda: self.testSave(self.ui.textBrowser_result))
        self.ui.pushButton_quit.clicked.connect(self.closeEvent)
        self.ui.show()

    def printCorrectPercentage(self, textbrowser, database, aux_array, matching):
        f = open('temp.txt', 'w')
	#textbrowser.clear()
        correct_num = 0
        targets = len(database)
        for row in range(targets):
            try:
                if database[row][0] == aux_array[max(matching[row], key=matching[row].get)][0]:
                    correct_num += 1
                if database[row][0] != aux_array[max(matching[row], key=matching[row].get)][0]:
                    f.write(str(database[row])+'\n')
            except:
                pass
        f.write('total: ' + str(targets))
        f.write('correct: ' + str(correct_num))
        f.write('percentage: ' + str((correct_num * 100) / targets) + '%')
        #textbrowser.append('total: ' + str(targets))
        #textbrowser.append('correct: ' + str(correct_num))
        #textbrowser.append('percentage: ' + str((correct_num * 100) / targets) + '%')

    def testSave(self, textBrowser_result):
        fname = QFileDialog.getSaveFileName(self, 'Save file', 'C:\\Users\shin\\Documents\\GitHub\\reident_project\\ex_result\\made_info')
        fhandle = open(fname[0], 'w')
        fhandle.write(textBrowser_result.toPlainText())
        fhandle.close()

    def totalrunFunction(self, textBrowser_percentage, textbrowser_result, database, aux_array, att_list, score_list, matching_list):
        self.runFunction(textBrowser_percentage, textbrowser_result, database, aux_array, att_list, score_list, matching_list)

    def setMatchingSet(self, input_matrix, output_matrix):
        for row in range(len(input_matrix)):
            output_matrix.append(dict())

    def matchingSet(self, input_array, alpha, output_array):
        for row in range(len(input_array)):
            for col in range(len(input_array[row])):
                if input_array[row][col] >= alpha:
                    output_array[row][col] = input_array[row][col]
            # print(row, output_array[row])

    def runFunction(self, textbrowser_percentage, textbrowser_result, database, aux_array, att_list, score_list, matching_list):
        textbrowser_result.append("de-anonymization alg is running ...")
        self.setScoreList(textbrowser_result, database, aux_array, score_list)
        self.getScore(database, aux_array, score_list)
        textbrowser_result.append("done")
        self.setMatchingSet(database, matching_list)
        eccentricity = 0.3
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

    def getScore(self, database, aux_array, output_list):
        progress_rate = 0
        len_database = len(database) / 100
        for record in range(len(database)):
            for aux in range(len(aux_array)):
                minimum = 1
                for attribute in range(len(aux_array[aux])):
                    if attribute == 0:
                        continue
                    res = self.sim(aux_array[aux][attribute], database[record][attribute])
                    if minimum > res:
                        output_list[record][aux] = round(res, 4)
                        minimum = round(res, 4)
            progress_rate += 1
            self.ui.progressBar.setValue(progress_rate / len_database)

    def setScoreList(self, textbrowser_result, database, aux_array, output_matrix):
        for row in range(len(database)):
            output_matrix.append([])
            for col in range(len(aux_array)):
                output_matrix[row].append(1)

    def fileOpen(self, output_matrix, textbrowser):
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            'C:\\Users\\shin\\PycharmProjects\\netflix\\input_data', '(*.csv)')
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
