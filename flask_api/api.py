import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


import threading
import json
import requests
import logging
from flask import Flask, request, jsonify
from algorithms.give_plans import run_algorithm



app = Flask(__name__)

@app.route('/send_data', methods=['POST'])
def receive_data():
    received_data = request.json
    ## 检查数据，到时与后端对接的时候再进一步考虑
    # if not received_data:
    #     # return jsonify({'status': 'error', 'message': 'No data received'})
    #     return jsonify({'status': 'error', 'message': '未接收到数据'})
    
    # if 'value1' not in received_data or 'value2' not in received_data:
    #     # return jsonify({'status': 'error', 'message': 'Missing required values'})
    #     return jsonify({'status': 'error', 'message': 'xx数据缺失'})
    
    # if received_data['value1'] is None or received_data['value2'] is None:
    #     # return jsonify({'status': 'error', 'message': 'Null values not allowed'})
    #     return jsonify({'status': 'error', 'message': 'xx数据不能为空值'})

    # response = {'status': 'success', 'message': 'Data received and stored successfully'}
    response = {'status': 'success', 'message': '成功接收数据'}
    ## 开始处理数据
    threading.Thread(target = run, args = (received_data, )).start()
    return jsonify(response)



def run(received_data):
    try:
        # 貌似不需要json.loads(),json格式的数据进来之后好像会自动转成Python字典
        received_data_dict = json.loads(received_data)
        # 算法运算，返回最终结果
        plans_result = run_algorithm(received_data_dict)

        # 结果计算完后调用后端接口，传回计算的方案结果
        send_processed_data_to_backend(plans_result)
    except Exception as e:
        logging.error(f'数据处理失败: {str(e)}')




def send_processed_data_to_backend(plans_result):
    ## 后端接口地址
    backend_api_url = 'http://backend-api-url.com/api'
    try:
        final_result = json.dumps(plans_result)
        response = requests.post(backend_api_url, json = final_result)
        if response.status_code == 200:
            logging.info('数据成功发送')
        else:
            logging.error(f'数据发送失败: {response.status_code}')
    except Exception as e:
        logging.error(f'发送数据到后端API失败: {str(e)}')


if __name__ == '__main__':
    app.run(debug = True)

