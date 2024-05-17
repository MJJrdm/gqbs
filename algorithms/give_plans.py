import pandas as pd
import time
import json
from .algorithm_helper import *
from .helper import give_plan_structure_dict
from loguru import logger

## 四个筛选标准，分别为钢厂、材质、厚度、镀层
filter_columns = ['mill', 'material_type', 'thickness', 'coating']

def data_preprocessing(received_data_dict):
    order_data = pd.DataFrame(received_data_dict['order_data'])
    parents_inventory_data = pd.DataFrame(received_data_dict['parents_inventory_data'])
    configuration_data = received_data_dict['configuration_data']
    ## 把钢厂字段为“TAGAL（广州）”全部替换成“TAGAL”
    order_data['mill'] = order_data['mill'].replace('TAGAL（广州）', 'TAGAL')
    parents_inventory_data['mill'] = parents_inventory_data['mill'].replace('TAGAL（广州）', 'TAGAL')

    # 四个筛选条件的所有唯一组合
    unique_combinations = order_data[filter_columns].apply(tuple, axis = 1).drop_duplicates()
    return order_data, parents_inventory_data, configuration_data, unique_combinations


##### 主函数，负责读取数据，计算出方案后输出方案以及加工计划
def run_algorithm(received_data_dict):
    start_time = time.time()
    order_data, parents_inventory_data, configuration_data, unique_combinations = data_preprocessing(received_data_dict)
    all_data_for_output = []
    counter = 1
    for combination in unique_combinations:
    
        ##### 过滤条件,四个条件分别为钢厂、材质、厚度、镀层
        combined_order_criteria = order_data[filter_columns].eq(combination).all(axis = 1)
        order_group_data = order_data[combined_order_criteria]

        # ##### 在订单内的零件对应订购方案的所有不重复的母材零件号列表
        # parent_id_in_order = list(order_group_data['母材零件号']['母材零件号子列'].drop_duplicates())
        # # parent_id_in_order -> ['MZ23021300007', 'MZ23090700035', 'M004188', 'M003465']
        # # print(parent_id_in_order)

        ##### 查找对应的库存母件数据（后续得注意字段名处理，以免字段名发生变化导致程序出错）
        combined_parents_criteria = parents_inventory_data[filter_columns].eq(combination).all(axis = 1)
        filter_parents_data = parents_inventory_data[combined_parents_criteria]
        
        ## 成品库存数据，目前不需要
        filter_components_storage_data = None

        weight_buffer = configuration_data['weight_buffer']

        ##### 处理订单、母件库存的原始数据，返回后续所需的信息
        (
        order_info_dict, ## 字典：订单上需要生产的零件相关信息，包括是否已经有裁切方案、零件宽度、零件所需出货重量等
        storage_info_dict, ## 字典：母件库存相关信息，包括母件钢卷号码、母件重量、母件宽度等
        parents_id_in_storage, ## 列表：库存里拥有的不重复出现的母材零件号
        same_components_required_weight, ## 字典：相同零件号在同一笔订单内所需的总出货重量
        parents_in_storage_width, ## 字典：储存每一个母材零件号对应的母材的宽度信息
        unique_component_width ## 字典：每一个零件号对应的零件宽度
        ) = data_preparation(order_group_data, filter_parents_data, weight_buffer)
    # {4: {'cut': False, 'component_number': 'PZ23072600004', 'width': 1444, 'weight_requirement': 11390.0, 'parent_id': '123456', 'fixed_weight_requirement': 11390.0}, 
    #  79: {'cut': False, 'component_number': 'PZ23072600004', 'width': 1444, 'weight_requirement': 31000.0, 'parent_id': '123456', 'fixed_weight_requirement': 31000.0}}
        
        ## min_waste为当母件裁切成多个零件时，当前工艺可控制达到的最小边损值，随着工艺的优化，min_waste的值可能会变小，之前是5，目前达到了4
        min_waste = configuration_data['min_waste']
        ## 母件库存信息字典不为空，存在对应规格（厚度、材质）跟对应钢厂的母材（不一定可以用来裁切，因为可能宽度不够）    
        if storage_info_dict:
            ## 获取这批组合零件的裁切方案
            plans = optimization(order_info_dict, storage_info_dict, filter_components_storage_data, 
                                 parents_id_in_storage, same_components_required_weight, 
                                 parents_in_storage_width, unique_component_width, min_waste, weight_buffer)
            print(f'方案{counter}: {plans}')
            
        ## 库存里不存在对应的可用来裁切母材
        else:
            # logger.info("不存在可用来裁切的母材")
            plans = [give_plan_structure_dict(components = [i for i in order_info_dict],
                                             components_output_weight = ['/' for _ in order_info_dict])]

            print(f'方案{counter}: {plans}')

    
        all_data_for_output.append(plans)
        print('\n')
        counter += 1
        # if counter >= 20:
        #     break
    add_adjustable_info(all_data_for_output)
    add_all_info_to_plans(all_data_for_output, order_data, parents_inventory_data)
    final_result = []
    for group in all_data_for_output:
        for plan in group:
            final_result.append(plan)
    end_time = time.time()
    print(f'花费时间：{round(end_time - start_time)}秒')
    return final_result





