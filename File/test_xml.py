# coding=utf-8

import os
import xmltodict


def xml_parser(f):
    print(f)
    with open(f) as fd:
        obj = xmltodict.parse(fd.read())
    print("x =",obj['x:recording']['@xmlns:x'])
    print("ref =",obj['x:recording']['@x:ref'])
    print("version =",obj['x:recording']['@x:version'])
    
    print("finalized =",obj['x:recording']['x:finalized'])
    print("master =",obj['x:recording']['x:master'])
    print("keepflag =",obj['x:recording']['x:keepflag'])
    print("rollbackrequired =",obj['x:recording']['x:rollbackrequired'])
    print("rollbacktime =",obj['x:recording']['x:rollbacktime'])
    print("compressiontype =",obj['x:recording']['x:compressiontype'])
    print("compressed =",obj['x:recording']['x:compressed'])
    print("rollbackid =",obj['x:recording']['x:rollbackid'])
    
    print("contenttype =",obj['x:recording']['x:segment']['x:contenttype'])
    print("capturetype =",obj['x:recording']['x:segment']['x:capturetype'])
    print("starttime =",obj['x:recording']['x:segment']['x:starttime'])
    
    for i in obj['x:recording']['x:segment']['x:attributes']['x:tag']:
        if '@x:taggedby' not in i.keys():
            print("timestamp =",i['@x:timestamp'])
            print("key =",i['x:attribute']['@x:key'])
            print("attribute =",i['x:attribute']["#text"])
        else:
            print("taggedby =",i['@x:taggedby'])
            print("timestamp =",i['@x:timestamp'])
            
            if isinstance(i['x:attribute'],list):
                for j in i['x:attribute']:
                    print("key =",j['@x:key'])
                    print("attribute =",j["#text"])
            else:
                print("key =",i['x:attribute']['@x:key'])
                print("attribute =",i['x:attribute']["#text"])
    
    print("systemtype =",obj['x:recording']['x:segment']['x:systemtype'])
    print("systemtype =",obj['x:recording']['x:segment']['x:multipart']['x:primary'])
    print("systemtype =",obj['x:recording']['x:segment']['x:duration'])
    
    
    print("session id =",obj['x:recording']['x:session']['@x:id'])
    print("session taggedby =",obj['x:recording']['x:session']['@x:taggedby'])
    
    print("contact id =",obj['x:recording']['x:contact']['@x:id'])
    print("contact taggedby=",obj['x:recording']['x:contact']['@x:taggedby'])
    
if __name__ == '__main__':
    dir = "C:\\Users\\Admin\\Desktop\\xml"
    for i in os.listdir(dir):
        if i[-3:] =='xml':
            xml_parser(os.path.join(dir,i))
