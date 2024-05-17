import math
import numpy as np
import pandas as pd
from minizinc import Instance, Solver
from .minizinc_model import *
from .helper import give_plan_structure_dict
# from openpyxl.styles import Alignment

##### 预处理订单数据以及母件库存数据，预处理后的数据作为算法输入数据
def data_preparation(order_group_data, filter_parents_data, weight_buffer):

    order_info_dict = {
                        i: {
                            'cut': False, # 是否已完成裁切
                            'component_number': order_group_data['component_number'].loc[i], # 零件号
                            'width': order_group_data['width'].loc[i], # 宽度
                            'weight_requirement': order_group_data['order_weight'].loc[i], # 剩余出货重量（会在优化过程中被持续更新）
                            'fixed_weight_requirement': order_group_data['order_weight'].loc[i], # 订单上所需的出货重量（不会被更新）
                            'storage_weight': order_group_data['inventory_weight'].loc[i], # 库存内成品重量
                            'already_output_weight': order_group_data['already_output_weight'].loc[i], # 已出库重量
                            'is_test_component': order_group_data['test_or_not'].loc[i], # 是否为调试材
                            'used_storage_components_info': {}, # 使用的库存成品信息，初始化为空字典
                            'used_storage_components_total_weight': 0, # 使用的库存成品总重量，初始化为0
                            'maximum_outer_radius': order_group_data['maximum_outer_radius'].loc[i]
                        } for i in order_group_data.index
                    }

    ##### 根据订单零件已出库重量，更新零件剩余所需出货重量
    for i, j in order_info_dict.items():
        if not np.isnan(j['already_output_weight']):
            ##### 该零件出货重量大于该零件所需出货重量时，把所需出货重量设为0，不直接减去出货重量，
            ##### 因为如果所需出货重量小于零，会影响该批订单里对应该零件号的零件所需的总出货重量
            ##### 而出货重量是针对某一个零件的，不是针对一批订单里的所有零件生产重量
            if j['already_output_weight'] >= j['weight_requirement']:
                j['weight_requirement'] = 0
                j['cut'] = True
            else:
                j['weight_requirement'] -= j['already_output_weight']


########################## 单元格内使用'调试材'字符串，后续可能会改格式，需要更改check_buffer_weight函数 ###############################
            ## 对非调试材，设置10%的缓冲，当剩余所需生产重量在总需生产重量10%范围内时无需再进行生产
            ## 对调试材，如果订单重量在1000kg以下，缓冲为10%，否则缓冲为50kg
            _ = check_buffer_weight(order_info_dict, i, weight_buffer)
########################## 单元格内使用'调试材'字符串，后续可能会改格式，需要更改check_buffer_weight函数 ###############################


    ##### 保存库存母材的基本信息，包括零件号、捆包号、母卷号、库存重量
    storage_info_dict = {
                            i: {
                                'component_number': filter_parents_data['parent_number'].loc[i], # 母材零件号
                                'coil_number': str(filter_parents_data['coil_number'].loc[i]), # 钢卷号
                                'bundle_number': str(filter_parents_data['bundle_number'].loc[i]), # 捆包号
                                'width': filter_parents_data['width'].loc[i], # 母卷宽度
                                'weight': int(filter_parents_data['weight'].loc[i]) # 母卷重量
                            } for i in filter_parents_data.index
                        }
    

    ## 库存里不存在对应的可用来裁切母材时，返回对应零件信息(order_info_dict)，提醒是哪些零件没有可以用来裁切的母材,其他数据均设为空值
    if not storage_info_dict:
        return (order_info_dict, None, None, None, None, None)
        

    ## 库存里拥有的母材的母材零件号（不重复出现）
    parents_id_in_storage = list(filter_parents_data['parent_number'].drop_duplicates())
    # parents_id_in_storage -> ['MZ23021300007', 'M004188', 'MZ22102500039', 'MZ22102500009', 'M003530']
    

    ## 每一个母材零件号对应的母材的宽度
    parents_in_storage_width = {i: int(filter_parents_data.loc[filter_parents_data['parent_number'] == i, 'width'].iloc[0]) for i in parents_id_in_storage}
    # parents_in_storage_width -> {'MZ23021300007': 1400, 'M004188': 970, 'MZ22102500039': 1115, 'MZ22102500009': 1458, 'M003530': 1260}


    ##### 每一个零件号对应的零件宽度
    unique_component_width = {}
    for i in order_info_dict:
        if order_info_dict[i]['component_number'] not in unique_component_width:
            unique_component_width[order_info_dict[i]['component_number']] = order_info_dict[i]['width']
    # unique_component_width -> {'PZ230201000019': 691, 'PZ23080800064': 270, 'PZ23080800050': 426, 'P009187': 481, 'PZ23080800006': 463}
            

    ##### 相同零件号在同一笔订单内所需的总出货重量
    same_components_required_weight = {i: 0 for i in unique_component_width}
    for i in order_info_dict:
        same_components_required_weight[order_info_dict[i]['component_number']] += order_info_dict[i]['weight_requirement']
    # same_components_required_weight -> {'PZ230201000019': 26547, 'PZ23080800064': 5000, 'PZ23080800050': 14448, 'P009187': 52000, 'PZ23080800006': 15000}


    return (order_info_dict, 
            storage_info_dict, 
            parents_id_in_storage, 
            same_components_required_weight, 
            parents_in_storage_width, 
            unique_component_width)



##### 根据输入处理过的订单数据、母件库存数据等输出裁切方案
def optimization(order_info_dict, storage_info_dict, filter_components_storage_data,
                 parents_id_in_storage, same_components_required_weight, parents_in_storage_width, 
                 unique_component_width, min_waste, weight_buffer):
    
    ## output_plans存储整个订单的所有裁切方案，后续可利用其作为方案输出
    output_plans = []


    ############################################### 暂时不使用库存 ###############################################
    ## 推荐使用库存成品，推荐结果于order_dict_info中显示
    # plans_using_components_storage(order_info_dict, filter_components_storage_data, unique_component_width)
    ############################################### 暂时不使用库存 ###############################################

    
    ## break_or_not为True时，代表库存里已经没有母件可以用来裁切，中止这一批筛选零件的方案计算，返回主程序继续下一批零件的方案计算
    break_or_not = False
    ## 按零件纳期日期顺序从前到后进行排刀
    for current_index in order_info_dict:

        ############################################### 暂时不使用库存 ###############################################
        ## 该订单对应零件使用了成品库存，添加备注信息
        if order_info_dict[current_index]['used_storage_components_info']:
            note = ''
            for used_component, used_component_weight in order_info_dict[current_index]['used_storage_components_info'].items():
                note += f'{used_component}: {used_component_weight}'
            note += f"总重量: {order_info_dict[current_index]['used_storage_components_total_weight']}"
            note += f"剩余出货重量: {order_info_dict[current_index]['weight_requirement']}"
            output_plans.append(give_plan_structure_dict(components = [current_index], note = note))
        ############################################### 暂时不使用库存 ###############################################


        ## 跳过已无需排刀的零件
        if order_info_dict[current_index]['cut'] == True:
            continue
        else:

            # 新添加1：记下哪些订单具有外径要求，需要单独进行零件裁切
            get_rid_of = []


            ##### 零件裁切重量还未满足订单纳期出库重量要求，对于量产零件，所剩需要出货重量在原本所需出货重量10%的范围内，
            ##### 则不用再进行排刀。对于非量产零件，若订单要求重量在1000kg以下，重量缓冲为10%，否则缓冲为50kg
            buffer = check_buffer_weight(order_info_dict, current_index, weight_buffer)
            while order_info_dict[current_index]['weight_requirement'] > buffer:                
                ## all_plans存储算法算出的方案
                all_plans = {}
                  
                ## 更新母件库存重量情况 
                parents_in_storage_weight = update_parents_in_storage_weight(storage_info_dict, parents_id_in_storage)
                # parents_in_storage_weight -> {'MZ23021300007': 42900.0, 'M004188': 7175.0, 'MZ22102500039': 8240.0, 'MZ22102500009': 26700.0, ...} 
                
                ##### 零件对应订购方案的母材零件号
                # current_parent_id = order_info_dict[current_index]['parent_id']
                # print(f'纳期最靠前且排刀未完成的零件编号: {current_index}\n',
                #       f'该纳期需要出货重量为：{order_info_dict[current_index]["fixed_weight_requirement"]}\n', 
                #       f'该纳期当前还需要重量为：{order_info_dict[current_index]["weight_requirement"]}\n',
                #       f'订单内该零件当前需要总出货重量为：{same_components_required_weight[order_info_dict[current_index]["component_number"]]}\n', sep = '')
                # 
                # ->    当前库存情况：{'MZ23021300007': 42900.0, 'M004188': 7175.0, 'MZ22102500039': 8240.0, 'MZ22102500009': 26700.0, 'M003530': 28240.0}
                #       纳期最靠前且排刀未完成的零件编号: 0
                #       该纳期需要出货重量为：13000
                #       该纳期当前还需要重量为：13000
                #       订单内该零件当前需要总出货重量为：26547
                             
                ##### terminate检查当前零件裁切重量是否已经满足所需的出货重量，若是，则不再进行裁切，直接跳过
                (current_components_needed_all_weight, terminate) = check_component_weight(current_index, order_info_dict, same_components_required_weight)
                if terminate:
                    order_info_dict[current_index]['cut'] = True
                    break           

                ##### 当前订购方案母材不在库，进行提示，all_plans里对于使用订购方案母件裁切在订单内的零件方案为空值
                # if current_parent_id not in storage_of_parent_id or parents_in_storage_weight[current_parent_id] < 20:
                #     print("订购方案母材不在库！！！")
                    
                ##### 裁切库存母材，break_or_not检查是否不存在任何方案，若为True，结束方案计算（此时存在厚度、钢厂、材质均符合的母材，但宽度可能不够）  
                # cut_parents_in_storage_plan会考虑get_rid_of列表里面的订单，如果current_index在列表里，
                # 那么只单独裁切这个零件，否则current_index可以和不在get_rid_of列表里的零件一起裁切
                break_or_not, all_plans['方案'] = cut_parents_in_storage_plan(order_info_dict, \
                                                                              parents_in_storage_width, \
                                                                              unique_component_width, \
                                                                              parents_in_storage_weight,
                                                                              min_waste, \
                                                                              get_rid_of)                
                if break_or_not:
                    print(f'{current_index}：不存在可以被用来裁切的母材！！！')
                    output_plans.append(give_plan_structure_dict(components = [current_index]))
                    break
            
                ##### chosse_plan提供可以从all_plans中选择具体方案的功能，返回plan_choice
                ##### plan_choice记录下哪个母材被使用，哪些零件被裁切，边损值之类的信息
                plan_choice = choose_plan(parents_id_in_storage, all_plans)
                # plan_choice -> {'parent_id': 'M004188', 'cut': [2, 0, 0, 0], 'components': [3, 5, 8, 11], 'obj': 8}


                # print(f'这是get_rid_of{get_rid_of}')
                ##### 自动设置零件裁切重量，相应裁切的母材重量以及与跟纳期最靠前零件搭配的其他零件的裁切重量会自动被算出，
                ##### 同时给出其他信息，比如裁切母件的钢卷号、母件裁切重量、零件产出重量等，但是不会更新母材、订单重量等
                (parent_coil_number, parent_bundle_number, parent_used_to_cut, parent_used_weight_in_kg, 
                 components_output_nums, components_output_weights, components_come_first,
                 same_components_required_weight) = cut_exact_info(current_index, storage_info_dict, plan_choice, 
                                                                   order_info_dict, parents_in_storage_width, 
                                                                   unique_component_width, same_components_required_weight, 
                                                                   current_components_needed_all_weight, get_rid_of)
                
                # 检查方案内是否所有产出成品的外径都满足条件，如满足，maximum_outer_radius_all_pass为True，get_rid_of为空列表
                # 如果不满足，maximum_outer_radius_all_pass为False，get_rid_of记录下是哪些成品外径不满足条件
                (maximum_outer_radius_all_pass, get_rid_of) = check_all_outer_radius(order_info_dict, components_output_nums, components_output_weights)


                 # 新添加2：所有成品外径均符合要求的情况下，可以更新母材、订单重量，并输出方案
                if maximum_outer_radius_all_pass: # 方案内所有的成品外径均符合要求
                    (weight, reduced_weights, parent_used_weight_in_kg) = update_weights(order_info_dict, 
                                                                                        storage_info_dict, 
                                                                                        parent_used_to_cut, 
                                                                                        parent_used_weight_in_kg, 
                                                                                        components_come_first, 
                                                                                        same_components_required_weight, 
                                                                                        components_output_nums, 
                                                                                        components_output_weights,
                                                                                        weight_buffer)
                    
                    ## 把方案输出成cut_info这种更容易理解的格式
                    cut_info = return_cut_solution(plan_choice, components_come_first, unique_component_width)
                    output_plans.append(give_plan_structure_dict(parent_coil_number = parent_coil_number,
                                                                 parent_bundle_number = parent_bundle_number,
                                                                 parent_used_weight_in_kg = parent_used_weight_in_kg,
                                                                 components = cut_info['cut_components_num'],
                                                                 components_output_weight = [weight] + [i for i in reduced_weights],
                                                                 cut_info = cut_info['plan_string'],
                                                                 note = '', 
                                                                 num_cut = cut_info['num_cut'],
                                                                 cut_num_for_each_component = cut_info['cut_num']))
                    # output_plans.append({'parent_coil_number': parent_coil_number, 
                    #                      'parent_bundle_number': parent_bundle_number,
                    #                      'parent_used_weight_in_kg': parent_used_weight_in_kg,
                    #                      'components': cut_info['cut_components_num'],
                    #                      'components_output_weight': [weight] + [i for i in reduced_weights],
                    #                      'cut_info': cut_info['plan_string'],
                    #                      'note': '没问题，很好',
                    #                      'num_cut': cut_info['num_cut'],
                    #                      'cut_num_for_each_component': cut_info['cut_num']})
                
                # 新添加3：不符合条件，什么都不做
                else: # 方案内存在不符合要求的成品外径
                    print(f'这是get_rid_of{get_rid_of}')
                    print(f'出问题了！！\n数目：{components_output_nums}\n重量：{components_output_weights}\n{components_come_first}')
                    pass

    for plan in output_plans:
        if plan['parent_coil_number'] != '/':
            for i in storage_info_dict.values():
                if i['coil_number'] == plan['parent_coil_number']:
                    plan['parent_remained_weight'] = int(i['weight'])

    return output_plans



##### 检查量产零件剩余所需生产重量是否在原本所需重量weight_buffer范围内，如果是，设置对应零件不再需要排刀，同时返回这个缓冲值
##### weight_buffer为百分比形式，例如10%、5%。
def check_buffer_weight(order_info_dict, current_index, weight_buffer):
    if order_info_dict[current_index]['is_test_component'] != '调试材':
        buffer = 0.01 * weight_buffer * order_info_dict[current_index]['fixed_weight_requirement']
    elif order_info_dict[current_index]['is_test_component'] == '调试材':
        if order_info_dict[current_index]['fixed_weight_requirement'] < 1000:
            buffer = 0.1 * order_info_dict[current_index]['fixed_weight_requirement']
        else:
            buffer = 50
    else:
        buffer = 0

    if order_info_dict[current_index]['weight_requirement'] <= buffer:
        order_info_dict[current_index]['cut'] = True

    return buffer



##### 计算母材裁切零件的方案
def cut_parents_in_storage_plan(order_info_dict, parents_in_storage_width, 
                                unique_component_width, parents_in_storage_weight, 
                                min_waste, get_rid_of):
    
    ## remain_temp为还没有完成裁切的零件编号列表
    remain_temp = [i for i in order_info_dict if order_info_dict[i]['cut'] == False]

    ########################################################################################################################
    # 检查当前零件在不在get_rid_of列表里面，如果在，只把这个零件放到remain里
    if remain_temp[0] in get_rid_of:
        remain = [remain_temp[0]]
    # 如果不在，那把上面的remain列表加上一个条件，只有不在get_rid_of里的零件才放入remain里，然后进行后面的裁切方案计算
    else:
        remain = [i for i in remain_temp if i not in get_rid_of]
    ########################################################################################################################
    

    ##### 不区分具有相同零件号的零件 -> ['P1', 'P5', 'P12', 'P51']
    unique_component_number_in_remain = []
    for i in remain:
        if order_info_dict[i]['component_number'] not in unique_component_number_in_remain:
            unique_component_number_in_remain.append(order_info_dict[i]['component_number'])
    

    ## 纳期最靠前的零件宽度
    first_component_width = unique_component_width[unique_component_number_in_remain[0]]
    parent_numbers = list(parents_in_storage_weight.keys()) # 母材零件号
    parents_width = list(parents_in_storage_width.values()) # 母材宽度
    num_parents = len(parents_width) # 母材数量
    num_components = len(unique_component_number_in_remain) # 需要裁切的零件数量
    components_width = [unique_component_width[i] for i in unique_component_number_in_remain] # 成品宽度
    all_cut_solutions = {}
    

    ##### 创建MiniZinc模型
    gecode = Solver.lookup("gecode")
    model = create_model()
    
    ## 对每一种在库母件零件号进行方案运算
    for j in range(1, num_parents + 1):        
        parent_width = parents_width[j-1]
        
        # 库存母件大于等于50kg的情况下才参与运算，母件宽度大于第一个零件的宽度才可能进行裁切，可以计算方案，否则直接跳过
        if parents_in_storage_weight[parent_numbers[j-1]] >= 50 and parent_width >= first_component_width:
            
            instance = Instance(gecode, model)
            instance['num_components'] = num_components
            instance['parent_width'] = parent_width
            instance['components_width'] = components_width
            instance['min_waste'] = min_waste
            # ##### 求出最佳优化函数值
            # with instance.branch() as opt:
            #     # opt.add_string(f"constraint used[{j}] = 1;\n")
            #     opt.add_string(f'solve minimize left;\n')
            #     res = opt.solve()
            #     ##### 可能无解，会给出空值，比如母件宽度比较小，需要裁切的零件宽度超过母件宽度
            #     try:
            #         best_objective = res["objective"]
            #     except:
            #         best_objective = None
            instance.add_string(f'solve minimize left + obj2;\n')
            result = instance.solve()
            obj = parent_width - sum([i * j for i, j in zip(result.solution.cut, components_width)])
            ## 识别到方案边损值小于等于x时，直接返回方案，不再进行计算（边损小于10可以看作是比较满意的拼刀了）
            x = 10
            if obj <= x:
                return (False, {j: {0: result.solution.cut, 'obj': obj}, 'components': unique_component_number_in_remain})
            all_cut_solutions[j] = {0: result.solution.cut}
            all_cut_solutions[j]['obj'] = obj
            # print(all_cut_solutions[j])

        else:
            all_cut_solutions[j] = {}
        # all_cut_solutions -> {1: {0: [3, 0, 0, 0], 'obj': 11}, 2: {}, 3: {0: [1, 1, 0, 0], 'obj': 171}, 4: {0: [1, 2, 0, 0], 'obj': 33}, ...}

    ##### 检查all_cut_solutions是否不存在任何方案，若是，则break_or_not为True  
    break_or_not = True
    for i in all_cut_solutions:
        break_or_not = not all_cut_solutions[i] and break_or_not
        
    all_cut_solutions['components'] = unique_component_number_in_remain

    return break_or_not, all_cut_solutions



##### 更新在库母材重量信息（后续寻求优化空间）
def update_parents_in_storage_weight(storage_info_dict, parents_id_in_storage):
    parents_in_storage_weight = {i: 0 for i in parents_id_in_storage}
    for i in storage_info_dict:
        parents_in_storage_weight[storage_info_dict[i]['component_number']] += storage_info_dict[i]['weight']
    return parents_in_storage_weight



##### 检查订单里相同零件号的零件的总出货重量是不是已经满足
def check_component_weight(current_index, order_info_dict, same_components_required_weight):
    component_number = order_info_dict[current_index]["component_number"]
    current_components_needed_weight = order_info_dict[current_index]['weight_requirement']
    current_components_needed_all_weight = same_components_required_weight[component_number]
    
    ## 订单内所有对应该零件的零件号的所有零件出货重量需求已经被满足的情况下，无需进行排刀
    terminate = False 
    if current_components_needed_all_weight <= 0:
        terminate = True
    if current_components_needed_weight <= 0:
        terminate = True    
    return (current_components_needed_all_weight, terminate)



##### 进行在使用不同母件裁切的不同方案中选择边损最小的方案
def choose_plan(parents_id_in_storage, all_plans):
    plans = all_plans['方案']
    # plans -> {1: {0: [3, 0, 0, 0], 'obj': 11}, 2: {}, 3: {0: [1, 1, 0, 0], 'obj': 171}, 4: {0: [1, 2, 0, 0], 'obj': 33}, ...}
    
    ##### 只存在1个方案时，直接返回该方案
    if len(list(plans.keys())) == 2:
        plan_index = list(plans.keys())[0] - 1
        return {
                'parent_id': parents_id_in_storage[plan_index],
                'cut': all_plans['方案'][plan_index+1][0], 
                'components': all_plans['方案']['components'], 
                'obj': all_plans['方案'][plan_index+1]['obj'],
                } 
    else:
        ## plans_obj存储每个方案的边损值
        plans_obj = []   
        
        for parent_used_to_cut in plans:
            if parent_used_to_cut != 'components' and plans[parent_used_to_cut]:
                objective = plans[parent_used_to_cut]['obj']
                plans_obj.append(objective)

        ## 拥有最小边损值裁切方案对应的母件索引
        index = plans_obj.index(min(plans_obj)) 
        the_list = [i for i in all_plans["方案"].keys() if all_plans["方案"][i]]
        plan_index = the_list[index] - 1
        plan_choice = {
                        'parent_id': parents_id_in_storage[plan_index],
                        'cut': all_plans['方案'][plan_index+1][0], 
                        'components': all_plans['方案']['components'], 
                        'obj': all_plans['方案'][plan_index+1]['obj'],
                    } 
        return plan_choice



# ##### 自动设定零件裁切重量，自动计算其他被搭配的零件裁切重量以及母材消耗重量，并自动更新母材在库重量、零件所需出库重量等信息，current_index没有用上，可以删掉
# def update_weight(current_index, storage_info_dict, plan_choice, order_info_dict, parents_in_storage_width, unique_component_width, same_components_required_weight, current_components_needed_all_weight):
#     # plan_choice -> {'parent_id': 'M004188', 'cut': [2, 0, 0, 0], 'components': ['P1', 'P2'], 'obj': 8}

#     ##### 裁切方案所使用的母材零件号以及所有在库的该类母材重量信息,只有在库重量超过xkg才会被选中，x可以设定为不同值
#     x = 5
#     current_parent_id = plan_choice['parent_id']
#     parents_weight_storage = {i: storage_info_dict[i]['weight'] for i in storage_info_dict 
#                               if storage_info_dict[i]['component_number'] == current_parent_id and storage_info_dict[i]['weight'] > x}
#     # parents_weight_storage -> {1: 8940.0, 2: 8930.0, 3: 7760.0, 4: 8460.0}

#     ##### 对应裁切方案的裁切零件编号（可能不被裁切）以及每个零件的要求宽度
#     components_group = plan_choice['components'] # ['P1', 'P2']
#     components_width = [unique_component_width[i] for i in components_group]
#     components_come_first = {}

#     ##### 具有裁切方案里的裁切零件号、纳期最靠前、且还未被裁切完的零件的编号
#     for i in order_info_dict:
#         the_component_number = order_info_dict[i]['component_number']
#         if order_info_dict[i]['cut'] is False and the_component_number not in components_come_first and the_component_number in components_group:
#             components_come_first[the_component_number] = i


#     ##### parents_weight_storage为非空的情况,即还存在可以裁切的母材
#     if parents_weight_storage: 
#         ## 按顺序进行母件的选择（入库时间最早）
#         parent_used_to_cut = list(parents_weight_storage.keys())[0]
#         parent_coil_number = storage_info_dict[parent_used_to_cut]['coil_number']
#         ## parent_weight为用来裁切的母材重量
#         parent_weight = parents_weight_storage[parent_used_to_cut]
#         ## 母件宽度
#         parent_width = parents_in_storage_width[current_parent_id]


#         ##### first_weight_percentage为纳期最靠前的零件裁切宽度占母件宽度的比例
#         cut_result = plan_choice['cut']
#         reduced_weights = []
#         components_have_maximum_outer_radius = []
#         for i in range(len(cut_result)):
#             if cut_result[i] != 0:
#                 base_width = cut_result[i] * components_width[i]
#                 weight_percentage = base_width / parent_width
#                 current_component_number = components_come_first[components_group[i]] # -> 49
#                 current_component_needed_weight = order_info_dict[current_component_number]["weight_requirement"] # 当前零件纳期所需的出货重量
#                 current_components_needed_all_weight = same_components_required_weight[order_info_dict[current_component_number]["component_number"]] # 当前零件纳期所需的总出货重量
#                 ## 最大可设定重量
#                 max_weight_in_kg = math.floor(weight_percentage * parent_weight)
#                 if current_component_needed_weight <= current_components_needed_all_weight:
#                     cut_weight = min(current_component_needed_weight, max_weight_in_kg)
#                 else:
#                     cut_weight = min(current_components_needed_all_weight, max_weight_in_kg)
                    
#                 parent_used_weight_temp = math.ceil(cut_weight / weight_percentage)

#                 if i == 0:
#                     reference_base_width = base_width
#                     reference_cut_weight = cut_weight
#                     parent_used_weight_in_kg = parent_used_weight_temp
#                     reference_index = 0
#                 else:
#                     if parent_used_weight_temp <= parent_used_weight_in_kg:
#                         reference_base_width = base_width
#                         reference_cut_weight = cut_weight
#                         parent_used_weight_in_kg = parent_used_weight_temp
#                         reference_index = i


#             # compute_outer_radius(total_weight, width, num, density = 7850, inner_radius = 508)


#         ##### 更新母材重量、被裁切的每个零件所需重量、每一个零件号对应零件所需的总剩余需求重量
#         ##### 母件库存重量多减去了15kg，为了避免后续生产人员可能要手动调整订单零件输出重量，这种方法是否可行？
#         storage_info_dict[parent_used_to_cut]['weight'] -= (parent_used_weight_in_kg + 15)
#         # order_info_dict[components_come_first[components_group[0]]]['weight_requirement'] -= weight
#         # same_components_required_weight[components_group[0]] -= weight
#         components_output_weights = {}
#         components_output_nums = {}
#         for i, j in enumerate(components_group):
#             if i == 0:
#                 if reference_index == 0:
#                     weight = reference_cut_weight
#                 else:
#                     weight = cut_result[0] * unique_component_width[j] / reference_base_width * reference_cut_weight
#                 components_output_weights[components_come_first[j]] = weight
#                 components_output_nums[components_come_first[j]] = cut_result[i]
#             else:
#                 if cut_result[i] != 0:
#                     if i != reference_index:
#                         weight = cut_result[i] * unique_component_width[j] / reference_base_width * reference_cut_weight
#                     else:
#                         weight = reference_cut_weight
#                     components_output_weights[components_come_first[j]] = weight
#                     components_output_nums[components_come_first[j]] = cut_result[i]

#         maximum_outer_radius_all_pass = True
#         get_rid_of = []
#         for i in components_output_weights:
#             if not np.isnan(order_info_dict[i]['maximum_outer_radius']):
#                 maximum_outer_radius = order_info_dict[i]['maximum_outer_radius']
#                 total_weight = components_output_weights[i]
#                 width = order_info_dict[i]['width']
#                 cut_num = components_output_nums[i]
#                 outer_radius = compute_outer_radius(total_weight, width, cut_num)
#                 if outer_radius <= maximum_outer_radius:
#                     pass
#                 else:
#                     get_rid_of.append[i]
#                     maximum_outer_radius_all_pass = False
#         return (maximum_outer_radius_all_pass, get_rid_of, components_output_weights, components_output_nums)

#         for i, j in enumerate(components_group):
#             if i == 0:
#                 if reference_index == 0:
#                     weight = reference_cut_weight
#                 else:
#                     weight = cut_result[0] * unique_component_width[j] / reference_base_width * reference_cut_weight
#                 order_info_dict[components_come_first[j]]['weight_requirement'] -= weight
#                 same_components_required_weight[j] -= weight
#             else:
#                 if cut_result[i] != 0:
#                     if i != reference_index:
#                         reduced_weight = cut_result[i] * unique_component_width[j] / reference_base_width * reference_cut_weight
#                     else:
#                         reduced_weight = reference_cut_weight
#                     order_info_dict[components_come_first[j]]['weight_requirement'] -= reduced_weight
#                     same_components_required_weight[j] -= reduced_weight
#                     reduced_weights.append(reduced_weight)


#         ##### 更新零件裁切状况，目前判断逻辑是当零件的出库重量要求满足后设定为已裁切完毕（cut = True），
#         for i in components_come_first.values():
#             _ = check_buffer_weight(order_info_dict, i)


#     ##### 母材数量不足，给出提示。后续需要考虑同时给出其他方案。
#     else:
#         print("母材数量不足！！！！")
    
#     return (parent_coil_number, components_come_first, weight, reduced_weights, parent_used_weight_in_kg)



##### 该函数计算裁切方案所输出的各零件重量，以及对应输出的卷数
def cut_exact_info(current_index, storage_info_dict, plan_choice, 
                   order_info_dict, parents_in_storage_width, 
                   unique_component_width, same_components_required_weight, 
                   current_components_needed_all_weight, get_rid_of):
    # plan_choice -> {'parent_id': 'M004188', 'cut': [2, 0, 0, 0], 'components': ['P1', 'P2'], 'obj': 8}

    ##### 裁切方案所使用的母材零件号以及所有在库的该类母材重量信息,只有在库重量超过xkg才会被选中，x可以设定为不同值
    x = 50
    current_parent_id = plan_choice['parent_id']
    parents_weight_storage = {i: storage_info_dict[i]['weight'] for i in storage_info_dict 
                              if storage_info_dict[i]['component_number'] == current_parent_id and storage_info_dict[i]['weight'] > x}
    # parents_weight_storage -> {1: 8940.0, 2: 8930.0, 3: 7760.0, 4: 8460.0}


    ##### 对应裁切方案的裁切零件编号（可能不被裁切）以及每个零件的要求宽度
    components_group = plan_choice['components'] # ['P1', 'P2']
    components_width = [unique_component_width[i] for i in components_group]
    components_come_first = {} 


    ##### 具有裁切方案里的裁切零件号、纳期最靠前、且还未被裁切完的零件的编号
    for i in order_info_dict:
        the_component_number = order_info_dict[i]['component_number']
        if order_info_dict[i]['cut'] is False and the_component_number not in components_come_first and the_component_number in components_group:
            components_come_first[the_component_number] = i
    # components_come_first -> {'P1': 21, 'P2': 47, 'P3': 71}

    ##### parents_weight_storage为非空的情况,即还存在可以裁切的母材
    if parents_weight_storage: 
        ## 按顺序进行母件的选择（入库时间最早）
        parent_used_to_cut = list(parents_weight_storage.keys())[0]
        parent_coil_number = storage_info_dict[parent_used_to_cut]['coil_number']
        parent_bundle_number = storage_info_dict[parent_used_to_cut]['bundle_number']
        ## parent_weight为用来裁切的母材重量
        parent_weight = parents_weight_storage[parent_used_to_cut]
        ## 母件宽度
        parent_width = parents_in_storage_width[current_parent_id]


        ##### first_weight_percentage为纳期最靠前的零件裁切宽度占母件宽度的比例
        cut_result = plan_choice['cut'] # [1, 2, 0, 0]
        is_the_first = True
        for i in range(len(cut_result)):
            if cut_result[i] != 0:
                base_width = cut_result[i] * components_width[i]
                weight_percentage = base_width / parent_width
                current_component_number = components_come_first[components_group[i]] # -> 49
                current_component_needed_weight = order_info_dict[current_component_number]["weight_requirement"] # 当前零件纳期所需的出货重量
                current_components_needed_all_weight = same_components_required_weight[order_info_dict[current_component_number]["component_number"]] # 当前零件纳期所需的总出货重量
                ## 最大可设定重量
                max_weight_in_kg = math.floor(weight_percentage * parent_weight)
                if current_component_needed_weight <= current_components_needed_all_weight:
                    cut_weight = min(current_component_needed_weight, max_weight_in_kg)
                else:
                    cut_weight = min(current_components_needed_all_weight, max_weight_in_kg)

                # print(f'这是get_rid_of{get_rid_of}')
                # print(f'这是current_index{type(current_index)}')

                # 新添加：当current_index在get_rid_of里面，需要注意裁切重量不能使得外径超过要求
                # 由于current_index在get_rid_of里面，在计算排刀方案的时候就已经保证只会裁切这一个零件，所以可以直接设置其重量
                if current_index in get_rid_of:
                    max_radius = order_info_dict[current_index]['maximum_outer_radius']
                    width = order_info_dict[current_index]['width']
                    num = cut_result[0]
                    ###########################################
                    # inner_radius = 
                    # density = 
                    # inner_radius和density后续可能需要人为设置 #
                    ###########################################
                    # 使成品外径不会超过要求上限的最大可裁切重量
                    max_weight_with_radius_requirement = max_weight_without_exceeding_outer_radius(max_radius, width, num)

                    if max_weight_with_radius_requirement < cut_weight:
                        cut_weight = max_weight_with_radius_requirement


                parent_used_weight_temp = math.ceil(cut_weight / weight_percentage)

                # 选择作为参考基准的成品
                if is_the_first is True:
                    reference_base_width = base_width
                    reference_cut_weight = cut_weight
                    parent_used_weight_in_kg = parent_used_weight_temp
                    reference_index = 0
                    is_the_first = False
                else:
                    if parent_used_weight_temp <= parent_used_weight_in_kg:
                        reference_base_width = base_width
                        reference_cut_weight = cut_weight
                        parent_used_weight_in_kg = parent_used_weight_temp
                        reference_index = i



        ##### 更新母材重量、被裁切的每个零件所需重量、每一个零件号对应零件所需的总剩余需求重量
        ##### 母件库存重量多减去了15kg，为了避免后续生产人员可能要手动调整订单零件输出重量，这种方法是否可行？


        # order_info_dict[components_come_first[components_group[0]]]['weight_requirement'] -= weight
        # same_components_required_weight[components_group[0]] -= weight


        ##### 记录下被裁切零件的输出重量、输出卷数信息
        components_output_weights = {}
        components_output_nums = {}
        for i, j in enumerate(components_group):
            if i == 0:
                if reference_index == 0:
                    weight = reference_cut_weight
                else:
                    weight = cut_result[0] * unique_component_width[j] / reference_base_width * reference_cut_weight
                components_output_weights[components_come_first[j]] = weight
                components_output_nums[components_come_first[j]] = cut_result[i]
            else:
                if cut_result[i] != 0:
                    if i != reference_index:
                        weight = cut_result[i] * unique_component_width[j] / reference_base_width * reference_cut_weight
                    else:
                        weight = reference_cut_weight
                    components_output_weights[components_come_first[j]] = weight
                    components_output_nums[components_come_first[j]] = cut_result[i]
        

        return (parent_coil_number, 
                parent_bundle_number,
                parent_used_to_cut, 
                parent_used_weight_in_kg, 
                components_output_nums,
                components_output_weights, 
                components_come_first,
                same_components_required_weight)
    

    ##### 母材数量不足，给出提示。后续需要考虑同时给出其他方案。
    else:
        print("母材数量不足！！！！")
        return (None, ) * 7



##### 该函数检查计划里是否存在具有最大上限外径要求的订单，如果存在，检查是否符合条件
def check_all_outer_radius(order_info_dict, components_output_nums, components_output_weights):
    # maximum_outer_radius_all_pass = True 代表具有外径上限的订单其输出成品的外径满足条件或者这批计划里不存在有这个条件的订单
    maximum_outer_radius_all_pass = True
    
    # get_rid_of 记下哪些零件（订单）不符合条件，后续单独进行裁切，不和其他零件一起进行裁切
    get_rid_of = []
    
    for i in components_output_weights:
        if order_info_dict[i]['maximum_outer_radius']:
            maximum_outer_radius = order_info_dict[i]['maximum_outer_radius']
            total_weight = components_output_weights[i]
            width = order_info_dict[i]['width']
            cut_num = components_output_nums[i]
            
            # 乘上0.001将单位毫米（mm）转化为单位米（m）（单位后面要注意，可能得统一一下）
            outer_radius = 0.001 * compute_outer_radius(total_weight, width, cut_num)
            if outer_radius <= maximum_outer_radius:
                pass
            else:
                get_rid_of.append(i)
                maximum_outer_radius_all_pass = False
    
    return (maximum_outer_radius_all_pass, get_rid_of)



##### 确定采用裁切方案后，进行母材、订单等的重量更新
def update_weights(order_info_dict, storage_info_dict, parent_used_to_cut, 
                   parent_used_weight_in_kg, components_come_first, 
                   same_components_required_weight, components_output_nums, components_output_weights, weight_buffer):
    
    ##### 更新母材重量、被裁切的每个零件所需重量、每一个零件号对应零件所需的总剩余需求重量
    ##### 母件库存重量多减去了15kg，为了避免后续生产人员可能要手动调整订单零件输出重量，这种方法是否可行？
    storage_info_dict[parent_used_to_cut]['weight'] -= (parent_used_weight_in_kg)
    reduced_weights = []
    for j, i in enumerate(components_output_nums.keys()):
        order_info_dict[i]['weight_requirement'] -= components_output_weights[i]
        same_components_required_weight[order_info_dict[i]['component_number']] -= components_output_weights[i]
        if j == 0:
            weight = components_output_weights[i]
        else:
            reduced_weights.append(components_output_weights[i])


    ##### 更新零件裁切状况，目前判断逻辑是当零件的出库重量要求满足后设定为已裁切完毕（cut = True），
    for i in components_come_first.values():
        _ = check_buffer_weight(order_info_dict, i, weight_buffer)

    return (weight, reduced_weights, parent_used_weight_in_kg)



######################### 计算裁切成品的外径，密度的数值是固定的，但是内径有508和610两种 #########################
def compute_outer_radius(total_weight, width, num, density = 7.85, inner_radius = 508):
    return np.sqrt(4000000 * total_weight / np.pi / width / num / density + inner_radius ** 2)



######################### 密度是固定的，数值为7850，内径有两种，508和610 #########################
##### 计算在成品外径不超过上限外径要求的情况下，当前该零件最多可输出的重量,保守起见，设置为95%
def max_weight_without_exceeding_outer_radius(max_radius, width, num, inner_radius = 508, density = 7.85):
    return 0.95 * ((1000 * max_radius) ** 2 - inner_radius ** 2) * np.pi * width * num * density / 4000000



##### 计算横切的可生产数量
def num_production(total_weight, length, width, thickness, density = 7.85):
    return 10**6 * total_weight / (length * width * thickness * density)




##### 把裁切方案处理成容易理解的格式
def return_cut_solution(plan_choice, components_come_first, unique_component_width):
    # plan_choice: {'parent_id': 'M004188', 
    #               'cut': [1, 1, 0, 0, 0], 
    #               'components': ['PZ230201000019', 'PZ23080800064', 'PZ23080800050', 'P009187', 'PZ23080800006'], 
    #               'obj': 9}
    
    # components_come_first: {'PZ230201000019': 0, 'PZ23080800064': 12, 'PZ23080800050': 37, 'P009187': 55, 'PZ23080800006': 57}
    
    cut = plan_choice['cut']
    # cut -> [1, 1, 0, 0, 0]
    
    components = plan_choice['components']
    # components -> ['PZ230201000019', 'PZ23080800064', 'PZ23080800050', 'P009187', 'PZ23080800006']
    
    cut_components_num = []
    cut_num = []
    for i, j in zip(cut, components):
        if i != 0:
            cut_num.append(i)
            # cut_num -> [1, 1] 

            cut_components_num.append(components_come_first[j]) 
            # cut_components_num -> [0, 1] 

    storage_components = list(range(len(components)))
    # storage_components -> [0, 1, 2, 3, 4]
    storage_components_width = [unique_component_width[i] for i in components]
    
    objective = plan_choice['obj']
    plan_string_list = [f'{cut[i]} * {storage_components_width[i]} + ' for i in storage_components if cut[i] != 0]
    plan_string = ''
    for string in plan_string_list:
        plan_string += string
    plan_string = plan_string + str(objective)
    num_cut = sum(cut_num)
    return {'cut_num': cut_num, 'cut_components_num': cut_components_num, 'plan_string': plan_string, 'num_cut': num_cut}



##### 负责将所有的方案输出成加工计划excel表格,但是这个excel表格的格式还是存在问题
def plans_to_intermediate_excel(all_data_for_output, order_data, parents_storage_data, raw_excel_file_path):
    columns_dict = {
    ('客户', '客户子列'): None,
    ('收货方', '收货方子列'): None,
    ('客户零件号', '客户零件号子列'): None,
    ('母材信息', '材质'): None,
    ('母材信息', '钢卷号'): None,
    ('母材信息', '厚度(mm)'): None,
    ('母材信息', '宽度(mm)'): None,
    ('母材信息', '长度(mm)'): None,
    ('母材信息', '净重(kg)'): None,
    ('母材信息', '钢厂'): None,
    ('加工信息', '厚度(mm)'): None,
    ('加工信息', '宽度(mm)'): None,
    ('加工信息', '长度(mm)'): None,
    ('加工信息', '数量(枚)'): None,
    ('加工信息', '净重(kg)'): None,
    ('加工信息', '张数/包'): None,
    ('加工信息', '纳期'): None,
    ('加工信息', '加工方式'): None,
    ('备注', '备注'): None,
    ('裁切组', '裁切组子列'): None,
    ('方案总刀数', '方案总刀数'): None,
    ('是否可调整', '是否可调整'): None,
    ('刀数', '刀数'): None
}
    
    columns = pd.MultiIndex.from_tuples(columns_dict.keys(), names = ['Category', 'Subcategory'])

    output_dataframe = pd.DataFrame(columns = columns, index = [])
    dataframe_index = 0
    for outer_index, each_category in enumerate(all_data_for_output):
        each_category.sort(key = lambda x: str(x['parent_coil_number']))
        for inner_index, each_plan in enumerate(each_category):
            each_plan['index'] = (outer_index, inner_index)

            parent_coil_number = each_plan['parent_coil_number']
            # print(parent_coil_number)
            if parent_coil_number and parent_coil_number != '/':
                parent_info = parents_storage_data.loc[parents_storage_data['钢卷号码'] == parent_coil_number, ['材质', '钢卷号码', '厚度', '幅度', '长度', '重量', '钢厂']]
            else:
                parent_info = None
            # print(parent_info)
            for index, component_num in enumerate(each_plan['components']):
                component_info = order_data.loc[component_num, [('客户', 'Unnamed: 3_level_1'), 
                                                               ('收货方', 'Unnamed: 4_level_1'), 
                                                               ('客户零件号', 'Unnamed: 5_level_1'),
                                                               ('材料尺寸（MM)', '厚'),
                                                               ('材料尺寸（MM)', '宽'),
                                                               ('材料尺寸（MM)', '长'),
                                                               ('订单数量', '数量'),
                                                               ('纳期', 'Unnamed: 12_level_1')]]

                output_dataframe.loc[dataframe_index, [('客户', '客户子列'), ('收货方', '收货方子列'), ('客户零件号', '客户零件号子列'),
                                                       ('加工信息', '厚度(mm)'), ('加工信息', '宽度(mm)'), ('加工信息', '长度(mm)'), 
                                                       ('加工信息', '数量(枚)'), ('加工信息', '纳期')]] = component_info.values
                if parent_info is not None:
                    if not parent_info.empty:
                        output_dataframe.loc[dataframe_index, [('母材信息', '材质'), ('母材信息', '钢卷号'), ('母材信息', '厚度(mm)'),
                                                            ('母材信息', '宽度(mm)'), ('母材信息', '长度(mm)'), ('母材信息', '净重(kg)'),
                                                            ('母材信息', '钢厂')]] = parent_info.values[0]
                    else:
                        output_dataframe.loc[dataframe_index, [('母材信息', '材质'), ('母材信息', '钢卷号'), ('母材信息', '厚度(mm)'),
                                                        ('母材信息', '宽度(mm)'), ('母材信息', '长度(mm)'), ('母材信息', '净重(kg)'),
                                                        ('母材信息', '钢厂')]] = '/'
                else:
                    output_dataframe.loc[dataframe_index, [('母材信息', '材质'), ('母材信息', '钢卷号'), ('母材信息', '厚度(mm)'),
                                                        ('母材信息', '宽度(mm)'), ('母材信息', '长度(mm)'), ('母材信息', '净重(kg)'),
                                                        ('母材信息', '钢厂')]] = '/'
                    
                output_dataframe.loc[dataframe_index, [('加工信息', '净重(kg)'), 
                                                       ('加工信息', '加工方式'),
                                                       ('裁切组', '裁切组子列'),
                                                       ('备注', '备注'),
                                                       ('方案总刀数', '方案总刀数'),
                                                       ('是否可调整', '是否可调整'),
                                                       ('刀数', '刀数')]] = (each_plan['components_output_weight'][index], 
                                                                            each_plan['cut_info'],
                                                                            str(each_plan['index']),
                                                                            each_plan['note'],
                                                                            each_plan['num_cut'],
                                                                            each_plan['adjustable'],
                                                                            each_plan['cut_num_for_each_component'][index])
                
                try:
                    length = output_dataframe.loc[dataframe_index, ('加工信息', '长度(mm)')]
                    total_weight = output_dataframe.loc[dataframe_index, ('加工信息', '净重(kg)')]
                    if length != 0 and total_weight != '/':
                        width = output_dataframe.loc[dataframe_index, ('加工信息', '宽度(mm)')]
                        thickness = output_dataframe.loc[dataframe_index, ('加工信息', '厚度(mm)')]
                        updated_num_production = num_production(total_weight, length, width, thickness)
                        output_dataframe.loc[dataframe_index, ('加工信息', '数量(枚)')] = updated_num_production
                    else:
                        output_dataframe.loc[dataframe_index, ('加工信息', '数量(枚)')] = np.nan
                except:
                    output_dataframe.loc[dataframe_index, ('加工信息', '数量(枚)')] = '/'
                    
                dataframe_index += 1
    

    # sorted_output_dataframe = output_dataframe.sort_values(by=[('刀数', '刀数'), ('裁切组', '裁切组子列'), ('加工信息', '加工方式')], ascending=[False, True, False] )
    
    # reread_data_raw = pd.read_excel(raw_excel_file_path, header = [0, 1])
    # reread_data = reread_data_raw.iloc[1:, 1:]
    # intermediate_excel_file_path = 'raw_plan.xlsx'
    # reread_data.to_excel(intermediate_excel_file_path)
    output_dataframe.to_excel(raw_excel_file_path, merge_cells = True)

    

# def merge_excel_file_and_output(raw_excel_file_path, final_excel_file_path):

#     data = pd.read_excel(raw_excel_file_path, header = [0, 1])
#     data = data.iloc[1:, :]

#     with pd.ExcelWriter(final_excel_file_path, engine = 'openpyxl') as writer:

#         data.to_excel(writer, sheet_name = 'Sheet1')

#         worksheet = writer.sheets['Sheet1']

#         for idx, row in data.iterrows():
#             if idx == 0:
#                 continue
#             elif idx == 1:
#                 previous_parent_coil_number = row[('母材信息', '钢卷号')]
#                 previous_cutting_group = row[('裁切组', '裁切组子列')]
#             else:
#                 current_parent_coil_number = row[('母材信息', '钢卷号')] 
#                 current_cutting_group = row[('裁切组', '裁切组子列')]
#                 if current_parent_coil_number == previous_parent_coil_number and current_parent_coil_number != '/':
#                     worksheet.merge_cells(start_row = idx + 2, end_row = idx + 3, start_column = data.columns.get_loc(('母材信息', '钢卷号')) + 2, end_column = data.columns.get_loc(('母材信息', '钢卷号')) + 2)
#                     worksheet.merge_cells(start_row = idx + 2, end_row = idx + 3, start_column = data.columns.get_loc(('母材信息', '厚度(mm)')) + 2, end_column = data.columns.get_loc(('母材信息', '厚度(mm)')) + 2)
#                     worksheet.merge_cells(start_row = idx + 2, end_row = idx + 3, start_column = data.columns.get_loc(('母材信息', '宽度(mm)')) + 2, end_column = data.columns.get_loc(('母材信息', '宽度(mm)')) + 2)
#                     worksheet.merge_cells(start_row = idx + 2, end_row = idx + 3, start_column = data.columns.get_loc(('母材信息', '长度(mm)')) + 2, end_column = data.columns.get_loc(('母材信息', '长度(mm)')) + 2)
#                     worksheet.merge_cells(start_row = idx + 2, end_row = idx + 3, start_column = data.columns.get_loc(('母材信息', '净重(kg)')) + 2, end_column = data.columns.get_loc(('母材信息', '净重(kg)')) + 2)
#                     worksheet.merge_cells(start_row = idx + 2, end_row = idx + 3, start_column = data.columns.get_loc(('母材信息', '钢厂')) + 2, end_column = data.columns.get_loc(('母材信息', '钢厂')) + 2)
#                 if current_cutting_group == previous_cutting_group and current_cutting_group != '/':
#                     worksheet.merge_cells(start_row = idx + 2, end_row = idx + 3, start_column = data.columns.get_loc(('加工信息', '加工方式')) + 2, end_column = data.columns.get_loc(('加工信息', '加工方式')) + 2)
#                 previous_parent_coil_number = current_parent_coil_number
#                 previous_cutting_group = current_cutting_group


#         for merged_range in worksheet.merged_cells.ranges:
#             for cell in merged_range:
#                 cell.alignment = Alignment(vertical='center', horizontal = 'center')



##### 负责处理库存数据，检验是否有成品库存，在有的情况下决定输出哪些库存等
def plans_using_components_storage(order_info_dict, filter_components_storage_data, unique_component_width, weight_buffer):
    # 零件号宽度: unique_component_width -> {'PZ230201000019': 691, 'PZ23080800064': 270}
 
    ##### order_info_with_storage_dict为存在库存的零件并且还需要进行裁切生产的零件字典
    order_info_with_storage_dict = {i: j for i, j in order_info_dict.items() 
                                    if ((not np.isnan(j['storage_weight'])) and (not j['cut']))}

    component_numbers_with_storage = [order_info_with_storage_dict[i]['component_number'] for i in order_info_with_storage_dict]
    # component_numbers_with_storage -> ['P2', 'P3', 'P6']
    
    component_groups = {i: [] for i in unique_component_width.keys() if i in component_numbers_with_storage}
    # component_groups -> {'P2': [], 'P3': [], 'P6': []}
    
    for i, j in order_info_with_storage_dict.items():
        com_num = j['component_number']
        component_groups[com_num].append(i)

    ##### 对每一组零件进行使用库存成品相关的计算
    for component_number in component_groups:
        # component_number -> P1, P2, P3......

        # 零件宽度
        width = unique_component_width[component_number]

        ## component_storage_info为满足宽度要求的成品相关数据
        component_storage_info = filter_components_storage_data[filter_components_storage_data['宽度'] == width]
        component_storage_info_dict = {i: {'factory_num': component_storage_info['加工厂编号'].loc[i],
                                           'weight': component_storage_info['重量'].loc[i]} for i in component_storage_info.index}

        # component_storage_weight -> 300kg
        # component_groups -> {'P1': [1, 2, 5], 'P2': [3, 6], 'P3': [0, 4]}  
        # component_groups_storage_weights -> {'P1': 5440, 'P2': 500, 'P3': 1200}
        for component in component_groups[component_number]:
            # component -> 零件对应的索引：0,1,2,3
            # print(component_storage_info_dict)

            ## component_storage_weight为该零件当前库存内拥有的成品重量，且保证库存成品重量在20kg以上才进行后续计算
            component_storage_weight = sum([i['weight'] for i in component_storage_info_dict.values()])
            
            # print(f'component_storage_weight: {component_storage_weight}')
            # print(component_storage_weight)
            if component_storage_weight >= 20:
                ##### 库存总量低于所需出货重量时，库存全部输出，所需出货重量减去库存重量，库存重量清零，同时检查零件所需出货重量是否在总需重量10%范围内
                if order_info_with_storage_dict[component]['weight_requirement'] >= component_storage_weight:
                    order_info_with_storage_dict[component]['weight_requirement'] -= component_storage_weight
                    # order_info_dict[component]['weight_requirement'] -= component_storage_weight

                    # 'used_storage_components_info': None, # 使用的库存成品信息，初始化为None
                    # 'used_storage_components_total_weight': 0 # 使用的库存成品总重量，初始化为0
                    ##### 更新库存成品重量并判断是否还需要裁切该零件
                    for j in component_storage_info_dict.values():
                        order_info_dict[component]['used_storage_components_info'][j['factory_num']] = [j['weight']]
                        j['weight'] = 0                         
                    order_info_dict[component]['used_storage_components_total_weight'] += component_storage_weight
                    _ = check_buffer_weight(order_info_dict, component, weight_buffer)
                    ## 库存已用完，退出循环
                    break
                
                else:
                    ##### 单卷成品重量大于x才参与运算
                    x = 50
                    factory_nums = [j['factory_num'] for j in component_storage_info_dict.values() if j['weight'] >= x]
                    indices = {j['factory_num']: i for i, j in component_storage_info_dict.items() if j['factory_num'] in factory_nums}
                    num_components = len(factory_nums)
                    components_weights = [int(j['weight']) for j in component_storage_info_dict.values() if j['weight'] >= x]
                    weight_requirement = int(order_info_with_storage_dict[component]['weight_requirement'])
                    buffer = check_buffer_weight(order_info_dict, component, weight_buffer)
                    try:
                        gecode = Solver.lookup("gecode")
                        model = create_storage_recommendation_model()
                        instance = Instance(gecode, model)
                        instance['num_components'] = num_components
                        instance['components_weights'] = components_weights
                        instance['weight_requirement'] = weight_requirement
                        instance['buffer'] = int(buffer)
                        instance.add_string(f'solve minimize abs(output_weight - weight_requirement);\n')
                        result = instance.solve()

                        ## 目前未使用obj
                        obj = result.objective         

                        ## used_storage_components表示对应库存零件是否被使用
                        used_storage_components = result.solution.used
                        # print(f'component_storage_weight: {component_storage_weight}')
                        # print(f'used_storage_components: {used_storage_components}')
                        # print(f'factory_nums: {factory_nums}')
                        # print(f'obj: {obj}\n')
                        ##### 更新库存数据，检查哪些成品被用掉了，用掉后清空
                        used_storage_components_info = order_info_dict[component]['used_storage_components_info']
                        for i, j in enumerate(factory_nums):
                            # i: 0, 1, 2, 3...
                            # j: F448, F153, F1258, F4881...
                            if used_storage_components[i] == 1:
                                used_storage_components_info[j] = components_weights[i]
                                order_info_dict[component]['used_storage_components_total_weight'] += components_weights[i]
                                component_storage_info_dict[indices[j]]['weight'] = 0
                        
                        ##### 更新成品库存数据以及零件出货重量        
                        order_info_with_storage_dict[component]['weight_requirement'] = 0
                        # order_info_dict[component]['weight_requirement'] = 0
                        _ = check_buffer_weight(order_info_dict, component, weight_buffer)
                    except:
                        print('有错误！！！')
            else:
                break   



def add_adjustable_info(all_data_for_output):
    for group_plans in all_data_for_output:  
        count = {}

        for plan in group_plans:
            count[plan['parent_coil_number']] = count.get(plan['parent_coil_number'], 0) + 1

        for plan in group_plans:
            if count[plan['parent_coil_number']] > 1 or plan['parent_coil_number'] == '/':
                plan['adjustable'] = 'no' 
            else:
                plan['adjustable'] = 'yes'



def add_all_info_to_plans(all_data_for_output, order_data, parents_inventory_data):
    order_keys_mapping = {
                          'customer': 'components_customer', 
                          'recipient': 'components_recipient', 
                          'customer_component_number': 'customers_component_number', 
                          'thickness': 'components_thickness', 
                          'width': 'components_width', 
                          'length': 'components_length', 
                          'delivery_time': 'components_delivery_time',
                          'component_number': 'components_number',
                          'component_name': 'components_name'
                        }
    
    final_order_keys_list = ['components_name', 'customer', 'recipient', 'customer_component_number', 'thickness', 'width', 'length', 'order_quantity', 'delivery_time']
    #  
    parents_keys_lit = ['parent_number', 'material_type', 'coil_number', 'parent_thickness', 'parent_width', 'parent_length', 'parent_weight', 'mill', 'coating']

    parents_keys_mapping = {'parent_number': 'parent_number',
                            'material_type': 'material_type',
                            'coil_number': 'coil_number',
                            'thickness': 'parent_thickness',
                            'width': 'parent_width',
                            'length': 'parent_length',
                            'weight': 'parent_weight',
                            'mill': 'mill',
                            'coating': 'coating',
                            'warehouse': 'warehouse'}
    
    final_parents_keys_list = ['parent_number', 'material_type', 'coil_number', 'parent_thickness', 'parent_width', 'parent_length', 'parent_weight', 'mill', 'coating', 'warehouse']
    parents_keys_list_original = list(parents_keys_mapping.keys())
    for outer_index, each_category in enumerate(all_data_for_output):
        each_category.sort(key = lambda x: str(x['parent_coil_number']))
        for inner_index, each_plan in enumerate(each_category):
            each_plan['group'] = str(tuple((outer_index, inner_index)))
            parent_coil_number = each_plan['parent_coil_number']
            if parent_coil_number and parent_coil_number != '/':
                parent_info = parents_inventory_data.loc[parents_inventory_data['coil_number'] == parent_coil_number, parents_keys_list_original]
            else:
                parent_info = None

            if parent_info is not None:
                if not parent_info.empty:
                    for parents_column_name_index, value in enumerate(parent_info.values[0]):
                        if isinstance(value, np.int64):
                            value = int(value)
                        each_plan[parents_keys_mapping[parents_keys_list_original[parents_column_name_index]]] = value
                else:
                    for i in list(parents_keys_mapping.values()):
                        each_plan[i] = '/'
            else:
                for i in list(parents_keys_mapping.values()):
                        each_plan[i] = '/'

            each_plan['coil_number'] = each_plan.pop('parent_coil_number')
            each_plan['bundle_number'] = each_plan.pop('parent_bundle_number')

            for index, component_num in enumerate(each_plan['components']):
                component_info = order_data.loc[component_num, list(order_keys_mapping.keys())]
                component_info_list = component_info.values.tolist()
                for order_column_name_index, value in enumerate(component_info_list):
                    if isinstance(value, np.int64):
                        value = int(value)
                    key = order_keys_mapping[list(order_keys_mapping.keys())[order_column_name_index]]
                    if key in each_plan:
                        each_plan[key].append(value)
                    else:
                        each_plan[key] = []
                        each_plan[key].append(value)
                each_plan['components_output_quantity'] = []
                try:
                    length = each_plan['components_length'][index]
                    total_weight = each_plan['components_output_weight'][index]
                    if length != 0 and total_weight != '/':
                        width = each_plan['components_width'][index]
                        thickness = each_plan['components_thickness'][index]
                        updated_num_production = num_production(total_weight, length, width, thickness)
                        each_plan['components_output_quantity'].append(updated_num_production)
                    else:
                        each_plan['components_output_quantity'].append(each_plan['cut_num_for_each_component'][index])
                except:
                    each_plan['components_output_quantity'].append(each_plan['cut_num_for_each_component'][index])