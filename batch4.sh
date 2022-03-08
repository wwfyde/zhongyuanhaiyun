#!/bin/bash

source /mydata/.venv/bin/activate

cd `dirname $0`
BASE_DIR="`pwd`"


python start_record_capture.py append 2022-02-26
python start_record_capture.py append 2022-02-27
python start_record_capture.py append 2022-02-28
python start_record_capture.py append 2022-03-01
python start_record_capture.py append 2022-03-02
python start_record_capture.py append 2022-03-03
#python start_record_capture.py append 2022-03-04
#python start_record_capture.py append 2022-03-05