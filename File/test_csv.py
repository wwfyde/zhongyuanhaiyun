#coding=utf-8

import codecs
import csv
import os
import sys

def read_CSV(path):
    with open(path.decode('utf-8'),'rb') as f:
        reader = csv.reader(f)
        row_list = []
        for row in reader:
            row_list.append(row)
        return row_list
        
#将列表写入文件
def writeFileByList(row_list,filepath):
#     try:
    res_list = []
    if (len(row_list)==0):
        return 0
    file_path=os.path.split(filepath)
    if( not os.path.exists(file_path[0])):
        os.makedirs(file_path[0])
    out = codecs.open(filepath, 'w', 'utf-8')
    #out = open('D:/csv.dim', 'w+')
    for line in row_list:
        tmp_list = ''
        for cell in line:
            tmp_list += (cell.decode('gbk').encode('utf-8').replace("|", "-").replace("\"", "").replace(",", "，").replace("\n", "").replace("\r", ""))+"|"
        res_list.append(tmp_list[:-1] + '\n')
    
    out.writelines(res_list)
    out.close()

if __name__ == '__main__':
    path = 'C:\\Users\\Admin\\Desktop\\接口字段设计.csv'
    
    writeFileByList(read_CSV(path),'C:\\Users\\ZhanLin\\Desktop\\接口字段设计.dim')