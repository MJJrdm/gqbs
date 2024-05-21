# 当一个母材只被用于一个排刀方案，且计划人员进行对算法输出的排刀方案进行调整时，
# 需要由算法计算相应的关联数据（母材投入重量、成品产出重量、数量等）变化结果，并进行相应调整；
# 当一个母材被用于多个排刀方案，且计划人员希望进行变动时，由计划人员自行进行方案的计算与调整。


import pandas as pd
import math


def main():
    ##### 读取排刀方案数据，排刀方案算法是从python列表或字典输出排刀方案excel表格，
    ##### 现在尝试从排刀excel表格到python列表或字典，然后调整python列表或字典，再进行输出，更换excel表格
    file_path = '########.xlsx' # excel表格路径
    df = pd.read_excel(file_path, header = [0, 1])
    fill_columns(df)
    all_plans = df_plans_to_dict(df)
    compute_width_proportion(all_plans)
    compute_maximum_output_weights(all_plans)
    group_nums = [2, 3, 6, 20, 22, 26] # 希望改变重量的零件所属裁切组
    indices = [0, 0, 0, 2, 0, 1] # 希望改变重量的零件在裁切组内所属位置索引
    setting_weights = [8000, 3700, 1000, 3000, 4210, 1000] # 调整的重量
    for group_num in group_nums:
        print(f"更改前重量：{all_plans[group_num]['components_output_weight']}\n更改前数量：{all_plans[group_num]['production_nums']}")

    # 调用函数调整成品产出重量
    adjust_plan_weights_and_production_nums(all_plans, group_nums, indices, setting_weights)
    
    for group_num in group_nums:
        print(f"更改后重量：{all_plans[group_num]['components_output_weight']}\n更改后数量：{all_plans[group_num]['production_nums']}")



##### 把dataframe的列名转为字典，键为列名，值为列的顺序（从1开始）
def col_names_to_dict(col_names):
    col_names_dict = {}
    for i, col_name in enumerate(col_names, 1):
        col_names_dict[col_name] = i
    return col_names_dict
# {('客户', '客户子列'): 1, ('收货方', '收货方子列'): 2, ('客户零件号', '客户零件号子列'): 3, ('母材信息', '材质'): 4, ......}



##### 给每一个裁切方案加上组号，为了后续进行排序的时候把同一个方案的计划排到一起以及合并同一个方案的单元格
##### 补充相同的母材信息
def fill_columns(df):
    df[('分组', '分组子列')] = None
    ##### 给每一个裁切方案加上组号，为了后续进行排序的时候把同一个方案的计划排到一起以及合并同一个方案的单元格
    current_number = 1
    parent_column_names = [('母材信息', '钢卷号'), ('母材信息', '厚度(mm)'), ('母材信息', '宽度(mm)'), ('母材信息', '长度(mm)'), ('母材信息', '净重(kg)'), ('母材信息', '钢厂')]
    for index, row in df.iterrows():
        if pd.isna(row[('加工信息', '加工方式')]):
            df.at[index, ('分组', '分组子列')] = df.at[index - 1, ('分组', '分组子列')]
            df.at[index, ('加工信息', '加工方式')] = df.at[index - 1, ('加工信息', '加工方式')]
        else:
            df.at[index, ('分组', '分组子列')] = current_number
            current_number += 1        

        if pd.isna(row[('母材信息', '钢卷号')]):
            for col_name in parent_column_names:
                df.at[index, col_name] = df.at[index - 1, col_name]



##### 生成后续更改方案成品产出重量流程所需信息字典格式
def create_plan_dict():
    plan_dict = {
                 'parent_coil_number': None, # 母材钢卷号
                 'parent_used_weight_in_kg': None, # 母材净重
                 'parent_width': None, # 母材宽度
                 'components': [], # 被裁切的成品编号
                 'components_output_weight': [], # 成品裁切输出重量
                 'components_widths': [], # 成品宽度
                 'components_lengths': [], # 成品长度，纵切工序长度显示为0
                 'components_thicknesses': [], # 成品厚度
                 'cut_info': None, # 裁切加工方式
                 'plan_cut_num': None, # 总拼刀数
                 'adjustable': None, # 是否可进行重量调整
                 'cut_num_for_each_component': [], # 每一个成品裁切输出的卷数
                 'group': None, # 计划属于哪个裁切组
                 'production_nums': [] # 横切生产数量
                }
    
    return plan_dict



##### 读取dataframe，把相应信息转换成字典形式存储
def df_plans_to_dict(df):
    all_plans = {}
    plan = {}
    for index, row in df.iterrows():
        if index == 0:
            old_group = row[('分组', '分组子列')]
            previous_row = row


        if row[('分组', '分组子列')] != old_group or index == 0:

            if not pd.isna(row[('母材信息', '钢卷号')]):
                parent_coil_number = row[('母材信息', '钢卷号')]
                parent_used_weight_in_kg = row[('母材信息', '净重(kg)')]
                parent_width = row[('母材信息', '宽度(mm)')]
            else:
                parent_coil_number = previous_row[('母材信息', '钢卷号')]
                parent_used_weight_in_kg = previous_row[('母材信息', '净重(kg)')]
                parent_width = row[('母材信息', '宽度(mm)')]

            plan = create_plan_dict()

            plan['parent_coil_number'] = parent_coil_number
            plan['parent_used_weight_in_kg'] = parent_used_weight_in_kg
            plan['parent_width'] = parent_width
            plan['components'].append(index)
            plan['components_output_weight'].append(row[('加工信息', '净重(kg)')])
            plan['components_widths'].append(row[('加工信息', '宽度(mm)')])
            plan['components_lengths'].append(row[('加工信息', '长度(mm)')])
            plan['components_thicknesses'].append(row[('加工信息', '厚度(mm)')])
            plan['cut_info'] = row[('加工信息', '加工方式')]
            plan['plan_cut_num'] = row[('方案总刀数', '方案总刀数')]
            plan['adjustable'] = row[('是否可调整', '是否可调整')]
            plan['cut_num_for_each_component'].append(row[('刀数', '刀数')])
            plan['group'] = row[('分组', '分组子列')]
            plan['production_nums'].append(row[('加工信息', '数量(枚)')])
            old_group = row[('分组', '分组子列')]
            previous_row = row
            all_plans[row[('分组', '分组子列')]] = plan

        ##### 同组方案内的成品
        else:
            all_plans[row[('分组', '分组子列')]]['components'].append(index)
            all_plans[row[('分组', '分组子列')]]['components_output_weight'].append(row[('加工信息', '净重(kg)')])
            all_plans[row[('分组', '分组子列')]]['components_widths'].append(row[('加工信息', '宽度(mm)')])
            all_plans[row[('分组', '分组子列')]]['cut_num_for_each_component'].append(row[('刀数', '刀数')])
            all_plans[row[('分组', '分组子列')]]['components_lengths'].append(row[('加工信息', '长度(mm)')])
            all_plans[row[('分组', '分组子列')]]['components_thicknesses'].append(row[('加工信息', '厚度(mm)')])
            all_plans[row[('分组', '分组子列')]]['production_nums'].append(row[('加工信息', '数量(枚)')])

    return all_plans



##### 计算方案内成品的宽度占所使用母材的宽度的比例
def compute_width_proportion(all_plans):
    for plan in all_plans.values():
        plan['width_proportion'] = []
        parent_width = plan['parent_width']
        if parent_width and parent_width != '/':
            for component_width, cut_num in zip(plan['components_widths'], plan['cut_num_for_each_component']):
                plan['width_proportion'].append(int(component_width)  * int(cut_num) / int(parent_width))
        else:
            plan['width_proportion'].append('/')



##### 计算方案内每一个成品可输出的最大重量，先通过计算宽度占比，再计算可输出重量
def compute_maximum_output_weights(all_plans):
    for plan in all_plans.values():
        plan['maximum_adjustable_weights'] = []
        parent_used_weight_in_kg = plan['parent_used_weight_in_kg']
        adjustable = plan['adjustable']
        for proportion in plan['width_proportion']:
            if parent_used_weight_in_kg != '/' and adjustable == 'yes':
                plan['maximum_adjustable_weights'].append(math.floor(proportion * parent_used_weight_in_kg))
            else:
                plan['maximum_adjustable_weights'].append('/')


# 传入三个参数：group_nums, indices, setting_weights，均为列表。
# group_nums代表希望调整的成品重量属于哪些裁切组；
# indices代表希望调整的具体成品的重量属于某个裁切组的哪个位置；
# setting_weights为希望调整的重量。
# 首先是需要检查每一个group_num对应的方案是否可以调整重量，如果不可以，给出提示信息，不做任何变动；
# 如果可以，检查对应indices的成品是否可以被设定为setting_weights位置对应的重量，如果可以，调整其他对应成品的输出重量，如果不可以，给出提示信息，并跳过
def adjust_plan_weights_and_production_nums(all_plans, group_nums, indices, setting_weights):
    for group_num, index, setting_weight in zip(group_nums, indices, setting_weights):
        plan = all_plans[group_num]
        adjustable = plan['adjustable']
        maximum_adjustable_weight = plan['maximum_adjustable_weights'][index]
        # 检查裁切组内方案是否可以进行重量调整
        if adjustable == 'yes':
            # 检查设定重量是否超过最大可设置重量，超出给出提示信息
            if setting_weight > maximum_adjustable_weight:
                print(f'裁切组{group_num}成品{index}设定重量超出上限，不可调整')
            # 否则进行相应调整
            else:
                base = setting_weight / plan['width_proportion'][index]
                for i, _ in enumerate(plan['components_output_weight']): 
                    if i == index:
                        plan['components_output_weight'][i] = setting_weight
                    else:
                        plan['components_output_weight'][i] = base * plan['width_proportion'][i]

                    if plan['components_lengths'][i] != 0:
                        try:
                            total_weight = plan['components_output_weight'][i]
                            length = plan['components_lengths'][i]
                            width = plan['components_widths'][i]
                            thickness = plan['components_thicknesses'][i]
                            plan['production_nums'][i] = num_production(total_weight, length, width, thickness)
                        except:
                            pass

        else:
            print(f'算法不可自动裁切方案组{group_num}的调整结果，请手动调整')
        


##### 计算横切可生产数量
def num_production(total_weight, length, width, thickness, density = 7.85):
    return 10**6 * total_weight / (length * width * thickness * density)




if __name__ == '__main__':
    main()

