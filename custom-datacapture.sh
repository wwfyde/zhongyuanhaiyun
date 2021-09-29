#!/bin/bash

cd `dirname $0`
BASE_DIR="`pwd`"
RECORD_PROCESS="start_record_capture"
GUNICORN_PROCESS="gunicorn"

record_start() {
  echo "starting record_capture..."
  pid=$(ps -ef|grep $RECORD_PROCESS |grep -v grep |awk '{if(NR==1)print $2}')
  if [ -z $pid ]; then
    nohup python3 start_record_capture.py start >> $BASE_DIR/nohup.out 2>&1 &
    echo "success"
  else
    echo "record_capture already started, PID:[$pid]"
  fi
}

record_stop(){
  echo "stopping record_capture..."
  pid=$(ps -ef|grep $RECORD_PROCESS |grep -v grep |awk '{if(NR==1)print $2}')
  if [ -z $pid ]; then
    echo "no record_capture process, already stopped?"
  else
    kill -9 $pid
    echo "stopped"
  fi
}

record_status(){
  pid=$(ps -ef|grep $RECORD_PROCESS |grep -v grep |awk '{if(NR==1)print $2}')
  if [ -z $pid ]; then
    echo "record_capture is stopped"
  else
    echo "record_capture is running, PID:[$pid]"
  fi
}

gunicorn_start() {
  echo "starting gunicorn..."
  pid=$(ps -ef|grep $GUNICORN_PROCESS |grep -v grep |awk '{if(NR==1)print $2}')
  if [ -z $pid ]; then
    nohup gunicorn -c etc/gunicorn.conf.py Web.web_flask:app 2>> $BASE_DIR/nohup.out &
    echo "success"
  else
    echo "gunicorn already started, PID:[$pid]"
  fi
}

gunicorn_stop(){
  echo "stopping gunicorn..."
  pid=$(ps -ef|grep $GUNICORN_PROCESS |grep -v grep |awk '{if(NR==1)print $2}')
  if [ -z $pid ]; then
    echo "no gunicorn process, already stopped?"
  else
    kill -9 $pid
    sleep 2
    echo "stopped"
  fi
}

gunicorn_status(){
  pid=$(ps -ef|grep $GUNICORN_PROCESS |grep -v grep |awk '{if(NR==1)print $2}')
  if [ -z $pid ]; then
    echo "gunicorn is stopped"
  else
    echo "gunicorn is running, PID:[$pid]"
  fi
}

case $1 in
  start)
    if [ -z $2 ]; then
      record_start
      gunicorn_start
    elif [ $2 == "record" ]; then
      record_start
    elif [ $2 == "gunicorn" ]; then
      gunicorn_start
    fi
    ;;
  stop)
    if [ -z $2 ]; then
      record_stop
      gunicorn_stop
    elif [ $2 == "record" ]; then
      record_stop
    elif [ $2 == "gunicorn" ]; then
      gunicorn_stop
    fi
    ;;
  status)
    if [ -z $2 ]; then
      record_status
      gunicorn_status
    elif [ $2 == "record" ]; then
      record_status
    elif [ $2 == "gunicorn" ]; then
      gunicorn_status
    fi
    ;;
  restart)
    if [ -z $2 ]; then
      record_stop
      record_start
      gunicorn_stop
      gunicorn_start
    elif [ $2 == "record" ]; then
      record_stop
      record_start
    elif [ $2 == "gunicorn" ]; then
      gunicorn_stop
      gunicorn_start
    fi
    ;;
esac