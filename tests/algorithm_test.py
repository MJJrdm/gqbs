import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


import json
import pandas as pd
from datetime import datetime
from algorithms import give_plans

def run(received_data):
    received_data_dict = json.loads(received_data)
    plans_result = give_plans.run_algorithm(received_data_dict)
    # 转成json格式
    plans_result = json.dumps(plans_result)
    print(plans_result)

if __name__ == '__main__':
    order_data_file_path = 'E:/gqbs_data/1/筛选订单.xlsx'
    # order_data_file_path = 'E:/gqbs_data/2/筛选订单.xlsx'
    order_data = pd.read_excel(order_data_file_path, header = [0, 1])
    # print(order_data.columns)
    parents_inventory_data_file_path = 'E:/gqbs_data/1/筛选库存数据.xlsx'
    # parents_inventory_data_file_path = 'E:/gqbs_data/2/筛选库存数据.xlsx'
    parents_inventory_data = pd.read_excel(parents_inventory_data_file_path)
    parents_inventory_data['入库日期'] = pd.to_datetime(parents_inventory_data['入库日期'])

    order_mapping_dict = {
                            ('订单状态', 'Unnamed: 0_level_1'): 'order_status', 
                            ('车型', 'Unnamed: 1_level_1'): 'vahicle_model', 
                            ('零件号', 'Unnamed: 2_level_1'): 'component_number',
                            ('客户', 'Unnamed: 3_level_1'): 'customer',
                            ('收货方', 'Unnamed: 4_level_1'): 'recipient',
                            ('客户零件号', 'Unnamed: 5_level_1'): 'customer_component_number',
                            ('广汽牌号', 'Unnamed: 6_level_1'): 'material_type',
                            ('材料尺寸（MM)', '厚'): 'thickness',
                            ('材料尺寸（MM)', '宽'): 'width',
                            ('材料尺寸（MM)', '长'): 'length',
                            ('订单数量', '数量'): 'order_quantity',
                            ('订单数量', '重量'): 'order_weight',
                            ('纳期', 'Unnamed: 12_level_1'): 'delivery_time',
                            ('库存', '数量'): 'inventory_quantity',
                            ('库存', '重量'): 'inventory_weight',
                            ('出货', '数量'): 'already_output_quantity',
                            ('出货', '重量'): 'already_output_weight',
                            ('备注', '钢厂'): 'mill',
                            ('备注', '零件名称'): 'component_name',
                        }
       
    order_data_list = []
    for index, row in order_data.iterrows():
        row_dict = {order_mapping_dict[column]: value for column, value in row.items() if column in order_mapping_dict}
        row_dict['coating'] = 1
        row_dict['test_or_not'] = None
        row_dict['maximum_weight'] = None
        row_dict['minimum_weight'] = None
        row_dict['inner_radius'] = 508
        row_dict['maximum_outer_radius'] = None
        row_dict['delivery_time'] = row_dict['delivery_time'].strftime('%Y-%m-%d')
        order_data_list.append(row_dict)

    parents_mapping_dict = {'零件号': 'parent_number', 
                            '材质': 'material_type',
                            '钢卷号码': 'coil_number',
                            '厚度': 'thickness',
                            '幅度': 'width', 
                            '长度': 'length',
                            '重量': 'weight',
                            '钢厂': 'mill',
                            '卷数': 'quantity',
                            '入库日期': 'original_inventory_age',
                            '捆包状态': 'bundle_status'}
    
    parents_data_list = []
    today_date = datetime.today()

    for index, row in parents_inventory_data.iterrows():
        row_dict = {parents_mapping_dict[column]: value for column, value in row.items() if column in parents_mapping_dict}
        row_dict['coating'] = 1
        row_dict['bundle_number'] = 1
        row_dict['warehouse'] = 'MJJ'
        ## 看一下后端传进来母材数据之前能不能先给母材数据按照原始库龄排个序，
        ## 如果后端那边有难度，需要算法这边在进行运算前先进行一个排序
        days_elapsed = (today_date - row_dict['original_inventory_age']).days
        # days_elapsed = (today_date - row_dict['original_inventory_age']).apply(lambda x: x.days)

        row_dict['original_inventory_age'] = days_elapsed
        parents_data_list.append(row_dict)
    
    received_data_before = {}
    received_data_before['order_data'] = order_data_list
    received_data_before['parents_inventory_data'] = parents_data_list
    received_data_before['configuration_data'] = {'min_waste': 4, "weight_buffer": 10}
    received_data = json.dumps(received_data_before)
    run(received_data)