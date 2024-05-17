# from helper import *

# def optimization(order_info_dict, storage_info_dict, filter_components_storage_data,
#                  parents_id_in_storage, same_components_required_weight, parents_in_storage_width, unique_component_width, min_waste):
#     ## output_plans存储整个订单的所有裁切方案，后续可利用其作为方案输出
#     output_plans = []


#     ## 推荐使用库存成品，推荐结果于order_dict_info中显示
#     # plans_using_components_storage(order_info_dict, filter_components_storage_data, unique_component_width)
    

#                         ###############
#                         # get_rid_of应该放在哪里？放在
#                         ###############

    
#     ## break_or_not为True时，代表库存里已经没有母件可以用来裁切，中止这一批筛选零件的方案计算，返回主程序继续下一批零件的方案计算
#     break_or_not = False
#     ## 按零件纳期日期顺序从前到后进行排刀
#     for current_index in order_info_dict:
#         ## 该订单对应零件使用了成品库存，添加备注信息
#         if order_info_dict[current_index]['used_storage_components_info']:
#             note = ''
#             for used_component, used_component_weight in order_info_dict[current_index]['used_storage_components_info'].items():
#                 note += f'{used_component}: {used_component_weight}'
#             note += f"总重量: {order_info_dict[current_index]['used_storage_components_total_weight']}"
#             note += f"剩余出货重量: {order_info_dict[current_index]['weight_requirement']}"
#             output_plans.append({'parent_coil_number': '/', 
#                                  'parent_used_weight_in_kg': '/',
#                                  'components': [current_index],
#                                  'components_output_weight': ['/'],
#                                  'cut_info': '/',
#                                  'note': note,
#                                  'num_cut': 0})
            

#         ## 跳过已无需排刀的零件
#         if order_info_dict[current_index]['cut'] == True:
#             continue
#         else:
#             ##### 零件裁切重量还未满足订单纳期出库重量要求，对于量产零件，所剩需要出货重量在原本所需出货重量10%的范围内，
#             ##### 则不用再进行排刀。对于非量产零件，则不设置重量缓冲，需要生产够订单要求的重量（后续和邱工交流，可不可以也设置非量产零件的重量缓冲）

#             # 新添加1：
#             get_rid_of = []
#             ###################

#             buffer = check_buffer_weight(order_info_dict, current_index)
#             while order_info_dict[current_index]['weight_requirement'] > buffer:                
#                 ## all_plans存储算法算出的方案
#                 all_plans = {}
                  
#                 ## 更新母件库存重量情况
#                 parents_in_storage_weight = update_parents_in_storage_weight(storage_info_dict, parents_id_in_storage)
#                 # parents_in_storage_weight -> {'MZ23021300007': 42900.0, 'M004188': 7175.0, 'MZ22102500039': 8240.0, 'MZ22102500009': 26700.0, ...} 
                
                             
#                 ##### terminate检查当前零件裁切重量是否已经满足所需的总出货重量，若是，则不再进行裁切，直接跳过
#                 (current_components_needed_all_weight, terminate) = check_component_weight(current_index, order_info_dict, same_components_required_weight)
#                 if terminate:
#                     order_info_dict[current_index]['cut'] = True
#                     break           

#                 ##### 当前订购方案母材不在库，进行提示，all_plans里对于使用订购方案母件裁切在订单内的零件方案为空值
#                 # if current_parent_id not in storage_of_parent_id or parents_in_storage_weight[current_parent_id] < 20:
#                 #     print("订购方案母材不在库！！！")
                    
#                 ##### 裁切库存母材，break_or_not检查是否不存在任何方案，若为True，返回主程序（此时存在厚度、钢厂、材质均符合的母材，但宽度可能不够）
#                 # 在这里需要把get_rid_of列表传入，在裁切的时候不把在get_rid_of里的零件加入  
#                 break_or_not, all_plans['方案'] = cut_parents_in_storage_plan(order_info_dict, \
#                                                                               parents_in_storage_width, \
#                                                                               unique_component_width, \
#                                                                               parents_in_storage_weight,
#                                                                               min_waste, \
#                                                                               get_rid_of)    
                            
#                 if break_or_not:
#                     print(f'{current_index}：不存在可以被用来裁切的母材！！！')
#                     output_plans.append({'parent_coil_number': '/', 
#                                          'parent_used_weight_in_kg': '/',
#                                          'components': [current_index],
#                                          'components_output_weight': ['/'],
#                                          'cut_info': '/',
#                                          'note': '',
#                                          'num_cut': 0})
#                     break


#                 ##### chosse_plan提供可以从all_plans中选择具体方案的功能，返回plan_choice
#                 plan_choice = choose_plan(parents_id_in_storage, all_plans)
#                 # plan_choice -> {'parent_id': 'M004188', 'cut': [2, 0, 0, 0], 'components': [3, 5, 8, 11], 'obj': 8}


#                 (parent_coil_number, parent_used_to_cut, parent_used_weight_in_kg, 
#                  components_output_nums, components_output_weights, components_come_first,
#                  same_components_required_weight) = cut_exact_info(
#                                                                     storage_info_dict, plan_choice, order_info_dict, 
#                                                                     parents_in_storage_width, unique_component_width, 
#                                                                     same_components_required_weight, 
#                                                                     current_components_needed_all_weight
#                                                                     )
                
#                 (maximum_outer_radius_all_pass, get_rid_of) = check_all_outer_radius(order_info_dict, components_output_nums, components_output_weights)




#                 # 新添加2：所有成品外径均符合要求的情况下，可以更新母材、订单重量，并输出方案
#                 if maximum_outer_radius_all_pass: # 方案内所有的成品外径均符合要求
#                     (weight, reduced_weights, parent_used_weight_in_kg) = update_weights(
#                                                                                         order_info_dict, 
#                                                                                         storage_info_dict, 
#                                                                                         parent_used_to_cut, 
#                                                                                         parent_used_weight_in_kg, 
#                                                                                         components_come_first, 
#                                                                                         same_components_required_weight, 
#                                                                                         components_output_nums, 
#                                                                                         components_output_weights
#                                                                                         )
                        
#                     ## 把方案输出成cut_info这种更容易理解的格式
#                     cut_info = return_cut_solution(plan_choice, components_come_first, unique_component_width)

#                     output_plans.append({'parent_coil_number': parent_coil_number, 
#                           'parent_used_weight_in_kg': parent_used_weight_in_kg,
#                           'components': cut_info['cut_components_num'],
#                           'components_output_weight': [weight] + [i for i in reduced_weights],
#                           'cut_info': cut_info['plan_string'],
#                           'note': '没问题，很好',
#                           'num_cut': cut_info['num_cut']})
                
#                 # 新添加3：不符合条件，什么都不做
#                 else: # 方案内存在不符合要求的成品外径，需要用上get_rid_of列表
#                     pass

    
#     return output_plans




# ##### 该函数计算裁切方案所输出的各零件重量，以及对应输出的卷数
# def cut_exact_info(current_index, storage_info_dict, plan_choice, 
#                    order_info_dict, parents_in_storage_width, 
#                    unique_component_width, same_components_required_weight, 
#                    current_components_needed_all_weight, get_rid_of):
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
#     # components_come_first -> {'P1': 21, 'P2': 47, 'P3': 71}

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
                

#             #   (current_index, storage_info_dict, plan_choice, 
#             #    order_info_dict, parents_in_storage_width, 
#             #    unique_component_width, same_components_required_weight, 
#             #    current_components_needed_all_weight, get_rid_of)

#             # max_weight_without_exceeding_outer_radius(max_radius, width, num, inner_radius = 508, density = 7850)
            
#                 # 新添加：当current_index在get_rid_of里面，需要注意裁切重量不能使得外径超过要求
#                 if current_index in get_rid_of:
#                     max_radius = order_info_dict[current_index]['maximum_outer_radius']
#                     width = order_info_dict[current_index]['width']
#                     num = cut_result[0]

#                     ###########################################
#                     # inner_radius = 
#                     # density = 
#                     # inner_radius和density后续可能需要人为设置 #
#                     ###########################################

#                     max_weight_with_radius_requirement = max_weight_without_exceeding_outer_radius(max_radius, width, num)
                
#                     if max_weight_with_radius_requirement < cut_weight:
#                         cut_weight = max_weight_with_radius_requirement

#                 parent_used_weight_temp = math.ceil(cut_weight / weight_percentage)

#                 # 选择作为参考基准的成品
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


#         # order_info_dict[components_come_first[components_group[0]]]['weight_requirement'] -= weight
#         # same_components_required_weight[components_group[0]] -= weight


#         ##### 记录下被裁切零件的输出重量、输出卷数信息
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
        

#         return (parent_coil_number, 
#                 parent_used_to_cut, 
#                 parent_used_weight_in_kg, 
#                 components_output_nums,
#                 components_output_weights, 
#                 components_come_first,
#                 same_components_required_weight)
    

#     ##### 母材数量不足，给出提示。后续需要考虑同时给出其他方案。
#     else:
#         print("母材数量不足！！！！")
#         return (None, ) * 7
    


# ##### 该函数检查计划里是否存在具有最大上限外径要求的订单，如果存在，检查是否符合条件
# def check_all_outer_radius(order_info_dict, components_output_nums, components_output_weights):
#     # maximum_outer_radius_all_pass = True 代表具有外径上限的订单其输出成品的外径满足条件或者这批计划里不存在有这个条件的订单
#     maximum_outer_radius_all_pass = True
    
#     # get_rid_of 记下哪些零件（订单）不符合条件，后续单独进行裁切，不和其他零件一起进行裁切
#     get_rid_of = []
    
#     for i in components_output_weights:
#         if not np.isnan(order_info_dict[i]['maximum_outer_radius']):
#             maximum_outer_radius = order_info_dict[i]['maximum_outer_radius']
#             total_weight = components_output_weights[i]
#             width = order_info_dict[i]['width']
#             cut_num = components_output_nums[i]
            
#             # 乘上0.001将单位毫米（mm）转化为单位米（m）
#             outer_radius = 0.001 * compute_outer_radius(total_weight, width, cut_num)
#             if outer_radius <= maximum_outer_radius:
#                 pass
#             else:
#                 get_rid_of.append(i)
#                 maximum_outer_radius_all_pass = False
    
#     return (maximum_outer_radius_all_pass, get_rid_of)


# ##### 确定采用裁切方案后，进行母材、订单等的重量更新
# def update_weights(order_info_dict, storage_info_dict, parent_used_to_cut, 
#                    parent_used_weight_in_kg, components_come_first, 
#                    same_components_required_weight, components_output_nums, components_output_weights):
#      ##### 更新母材重量、被裁切的每个零件所需重量、每一个零件号对应零件所需的总剩余需求重量
#     ##### 母件库存重量多减去了15kg，为了避免后续生产人员可能要手动调整订单零件输出重量，这种方法是否可行？
#     storage_info_dict[parent_used_to_cut]['weight'] -= (parent_used_weight_in_kg + 15)
#     # order_info_dict[components_come_first[components_group[0]]]['weight_requirement'] -= weight
#     # same_components_required_weight[components_group[0]] -= weight
#     reduced_weights = []
#     for j, i in enumerate(components_output_nums.keys()):
#         order_info_dict[i]['weight_requirement'] -= components_output_weights[i]
#         same_components_required_weight[order_info_dict[i]['component_number']] -= components_output_weights[i]
#         if j == 0:
#             weight = components_output_weights[i]
#         else:
#             reduced_weights.append(components_output_weights[i])


#     ##### 更新零件裁切状况，目前判断逻辑是当零件的出库重量要求满足后设定为已裁切完毕（cut = True），
#     for i in components_come_first.values():
#         _ = check_buffer_weight(order_info_dict, i)

#     return (weight, reduced_weights, parent_used_weight_in_kg)


# # 需要用上get_rid_of列表，每一次进行方案运算前，先检查当前订单零件在不在get_rid_of列表里面，
# # 如果在，进行单独裁切。如果不在，该零件可以和其他零件一起进行裁切，但是不能和在get_rid_of
# # 列表里的零件一起进行裁切。想一想这个逻辑要怎么实现。
# # 在一轮循环开始时，检查当前零件在不在get_rid_of列表里面，如果在，模型需要设置其他零件裁切数均为0
# # 往minizinc模型中传入一个新的列表，这个列表的长度可能跟零件列表长度一样，为0代表可以一起裁切，
# # 为1代表不能一起裁切
# # get_rid_of列表里面存的是零件索引，可以在选择传入裁切零件的步骤的时候，就不选择在get_rid_of列表里的零件

# import numpy as np

# ##### 计算在成品外径不超过上限外径要求的情况下，当前该零件最多可输出的重量,保守起见，设置为98%
# def max_weight_without_exceeding_outer_radius(max_radius, width, num, inner_radius = 508, density = 7850):
#     return 0.98 * (max_radius - inner_radius) ** 2 * np.pi * width * num * density / 4000000000


# ##### 计算母材裁切零件的方案
# def cut_parents_in_storage_plan(order_info_dict, parents_in_storage_width, unique_component_width, 
#                                 parents_in_storage_weight, min_waste, get_rid_of):
    

#     ######################################## 修改remain，可能需要用上get_rid_of列表 ########################################
#     ## remain为还没有完成裁切的零件编号列表
#     remain_temp = [i for i in order_info_dict if order_info_dict[i]['cut'] == False]
#     ######################################## 修改remain，可能需要用上get_rid_of列表 ########################################


#     ########################################################################################################################
#     # 检查当前零件在不在get_rid_of列表里面，如果在，只把这个零件放到remain里
#     if remain_temp[0] in get_rid_of:
#         remain = [remain_temp[0]]
#     # 如果不在，那把上面的remain列表加上一个条件，只有不在get_rid_of里的零件才放入remain里，然后进行后面的裁切方案计算
#     else:
#         remain = [i for i in remain_temp if i not in get_rid_of]
#     ########################################################################################################################


#     #########
#                 ##
#                 ###



#     ##### 不区分具有相同零件号的零件
#     unique_component_number_in_remain = []
#     for i in remain:
#         if order_info_dict[i]['component_number'] not in unique_component_number_in_remain:
#             unique_component_number_in_remain.append(order_info_dict[i]['component_number'])

#     ## 纳期最靠前的零件宽度
#     first_component_width = unique_component_width[unique_component_number_in_remain[0]]
#     parent_numbers = list(parents_in_storage_weight.keys())
#     parents_width = list(parents_in_storage_width.values())
#     num_parents = len(parents_width)
#     num_components = len(unique_component_number_in_remain)
#     components_width = [unique_component_width[i] for i in unique_component_number_in_remain]
#     all_cut_solutions = {}
#     ##### 创建MiniZinc模型
#     gecode = Solver.lookup("gecode")
#     model = create_model()
    
#     ## 对每一种在库母件零件号进行方案运算
#     for j in range(1, num_parents + 1):        
#         ## 库存母件大于等于20kg的情况下才参与运算
#         parent_width = parents_width[j-1]
#         ##### 母件宽度大于第一个零件的宽度才可能进行裁切，可以计算方案，否则直接跳过
#         if parents_in_storage_weight[parent_numbers[j-1]] >= 20 and parent_width >= first_component_width:
#             instance = Instance(gecode, model)
#             instance['num_components'] = num_components
#             instance['parent_width'] = parent_width
#             instance['components_width'] = components_width
#             instance['min_waste'] = min_waste
#             # ##### 求出最佳优化函数值
#             with instance.branch() as opt:
#                 opt.add_string(f'constraint used[j] = 1;\n')
#                 opt.add_string(f'solve minimize left;\n')
#                 res = opt.solve()
#                 try:
#                     best_objective = res['objective']
#                 except:
#                     best_objective = None
#             # with instance.branch() as opt:
#             #     # opt.add_string(f"constraint used[{j}] = 1;\n")
#             #     opt.add_string(f'solve minimize left;\n')
#             #     res = opt.solve()
#             #     ##### 可能无解，会给出空值，比如母件宽度比较小，需要裁切的零件宽度超过母件宽度
#             #     try:
#             #         best_objective = res["objective"]
#             #     except:
#             #         best_objective = None
#             instance.add_string(f'solve minimize left;\n')
#             result = instance.solve()
#             obj = result.objective
#             ## 识别到方案边损值小于等于x时，直接返回方案，不再进行计算
#             x = 10
#             if result.objective <= x:
#                 return (False, {j: {0: result.solution.cut, 'obj': obj}, 'components': unique_component_number_in_remain})
#             all_cut_solutions[j] = {0: result.solution.cut}
#             all_cut_solutions[j]['obj'] = obj
#             # print(all_cut_solutions[j])

#         else:
#             all_cut_solutions[j] = {}
#         # all_cut_solutions -> {1: {0: [3, 0, 0, 0], 'obj': 11}, 2: {}, 3: {0: [1, 1, 0, 0], 'obj': 171}, 4: {0: [1, 2, 0, 0], 'obj': 33}, ...}


#     ##### 检查all_cut_solutions是否不存在任何方案，若是，则break_or_not为True，返回主程序  
#     break_or_not = True
#     for i in all_cut_solutions:
#         break_or_not = not all_cut_solutions[i] and break_or_not

#     all_cut_solutions['components'] = unique_component_number_in_remain

#     return break_or_not, all_cut_solutions 









 
 
 


