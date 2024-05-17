# json需求数据格式：三个键分别为'order_data', 'parents_inventory_data'，'configuration_data'
# 分别代表订单数据、母材库存数据、算法配置数据
# 键'order_data'和'parents_inventory_data'对应的值均为列表，列表每一条数据为一个字典，代表一条订单数据或一条母材数据，
# 键'configuration_data'对应的值为一个字典，排刀算法当前只有两个配置项，所以字典有两对键与值

### 可能加上唯一标识符更好？或者就这样在计算方案的时候把所有信息都加上去再返回来
{'order_data': [{
                 '钢厂': None,
                 '纳期': None,
                 '客户': None,
                 '车型': None,
                 '内径': None, 
                 '零件号': None, 
                 '收货方': None, 
                 '订单状态': None,
                 '广汽牌号': None, 
                 '材料厚度': None, 
                 '材料宽度': None, 
                 '材料长度': None,
                 '材料镀层': None,
                 '订单重量': None,
                 '订单数量': None,
                 '库存重量': None,
                 '库存数量': None,
                 '出货重量': None,
                 '出货数量': None,
                 '客户零件号': None,
                 '是否为调试材': None,
                 '单卷重量上限': None,
                 '单卷重量下限': None,
                 '排刀外径上限': None
                 }], 
 'parents_inventory_data': [{
                             '厚度': None,
                             '宽度': None,
                             '长度': None,
                             '仓库': None,
                             '卷数': None,
                             '重量': None,
                             '钢厂': None,
                             '材质': None,
                             '镀层': None,
                             '零件号': None,
                             '捆包号': None,
                             '钢卷号': None,
                             '捆包状态': None,
                             '存货性质': None,
                             '原始库龄': None,
                             '捆包库龄': None,
                             }],
 'configuration_data': {}}

{'order_data': [{'order_status': None,  # str    订单状态
                 'vehicle_model': None,  # str    车型
                 'component_number': None,  # str    零件号
                 'customer': None,  # str    客户
                 'recipient': None,  # str    收货方
                 'customer_component_number': None,  # str    客户零件号
                 'mill': None,  # str    钢厂
                 'material_type': None,  # str    材质
                 'thickness': None,  # float(2)    (mm)    厚度
                 'width': None,  # int    (mm)    宽度
                 'length': None,  # int    (mm)    长度
                 'coating': None,  # str    镀层
                 'order_weight': None,  # float/int    (kg)    订单重量
                 'order_quantity': None,  # int    (None/片)    订单数量
                 'delivery_time': None,  # time    纳期
                 'inventory_weight': None,  # float/int    (kg)    库存重量
                 'inventory_quantity': None,  # int    (None/片)    库存数量
                 'already_output_weight': None,  # float/int    (kg)    已出货重量
                 'already_output_quantity': None,  # int    (None/片)    已出货数量
                 'test_or_not': None,  # str    是否是调试件
                 'maximum_weight': None,  # float/int    (kg)    单卷重量上限
                 'minimum_weight': None,  # float/int    (kg)    单卷重量下限
                 'inner_radius': None,  # int    (mm)    内径
                 'maximum_outer_radius': None  # int    (mm)    最大外径
                 }, {}, {}, {}, {}], 
 'parents_inventory_data': [{'parent_number': None,  # str    母材零件号
                             'bundle_number': None,  # str    捆包号
                             'coil_number': None,  # str    钢卷号
                             'thickness': None,  # float(2)    (mm)    厚度
                             'width': None,  # int    (mm)    宽度
                             'length': None,  # int    (mm)    长度
                             'quantity': None,  # int    (卷)    数量
                             'weight': None,  # flaot/int    (kg)    重量
                             'mill': None,  # str    钢厂
                             'material_type': None,  # str    材质
                             'coating': None,  # str    镀层
                             'bundle_status': None,  # str    捆包状态
                             'inventory_property': None,  # str    存货性质
                             'original_inventory_age': None,  # int    (天)    原始库龄
                             'bundle_age': None,  # int    (天)    捆包库龄
                             'warehouse': None  # str    仓库
                             }, {}, {}, {}, {}],
 'configuration_data': {'min_waste': 4, 'weight_buffer': 10}}



# 回传排刀方案数据格式
# json字典，每一条数据为一个字典，代表一个方案，包含该方案使用的母材及相关信息，以及被裁切的零件及零件的相应信息，零件可能有多个
{ 'plans':[{
          'parent_number': None,  # str    母材零件号
          'bundle_number': None,  # str    捆包号
          'coil_number': None,  # str    钢卷号
          'parent_weight': None,  # float/int    (kg)    母材重量
          'parent_thickness': None,  # float(2)    (mm)    母材厚度
          'parent_width': None,  # int    (mm)    母材宽度
          'parent_length': None,  # int    (mm)    母材长度
          'warehouse': None,  # str    母材仓库
          'mill': None,  # str    钢厂
          'material_type': None,  # str    材质
          'coating': None,  # str    镀层
          'components': [0, 4, 15], # list of int    (None)    订单成品索引
          'components_name': [],  # list of str    零件名称列表
          'components_output_weight': [218, 452, 385],  # list of float/int    (kg)    成品产出重量列表
          'components_thickness': [],  # list of float(2)    (mm)    成品厚度列表
          'components_width': [],  # list of int    (mm)    成品宽度列表
          'components_length': [],  # list of int    (mm)    成品长度列表
          'components_output_quantity': [],  # list of int    (卷/片)    成品产出卷数（纵切）或片数（横切） 
          'components_delivery_time': [],  # list of time    纳期 
          'components_customer': [],  # list of str    客户
          'components_recipient': [], # list of str 收货方
          'components_number': [], # list of str 成品零件号
          'customers_component_number': [],  # list of str    客户零件号
          'cut_info': '260 + 500 + 2 * 300 + 5',  # str    排刀方案 
          'note': '',  # str    备注信息      
          'num_cut': 4,  # int    (卷)    刀数
          'cut_num_for_each_component': []  # list of int    (卷)    成品产出卷数列表
          }, {}, {}],
  'logs': ['日志信息1', '日志信息2', '日志信息3', ...]}
 
{
 "note": "\u6ca1\u95ee\u9898\uff0c\u5f88\u597d", 
 "num_cut": 2, 
 "cut_num_for_each_component": [2], 
 "adjustable": "yes", 
 "group": "(0, 0)", 
 "parent_number": "MZ22080400028",
 "material_type": "GX420LAD+ZF", 
 "coil_number": "D1123911803101", 
 "parent_thickness": 1.0, 
 "parent_width": 1343, 
 "parent_length": "C", 
 "parent_weight": 2350, 
 "mill": "\u9996\u94a2", 
 "coating": 1, 
 "warehouse": "MJJ", 
 "bundle_number": "1",
 "components_customer": ["\u5fb7\u5065\u81ea\u8d2d"], 
 "components_recipient": ["\u5fb7\u5065\u81ea\u8d2d"], 
 "customers_component_number": ["4030543CMV0000"], 
 "components_thickness": [1.0], 
 "components_width": [669], 
 "components_length": [0], 
 "components_delivery_time": ["2024-02-03"], 
 "components_number": ["PZ22060100020"], 
 "components_name": ["\u540e\u5730\u677f\u7b2c\u4e94\u6a2a\u6881"], 
 "components_output_quantity": [2]
}



{"parent_used_weight_in_kg": 3013, 
 "components": [70], 
 "components_output_weight": [3000.0], 
 "cut_info": "1 * 1200 + 5", 
 "note": "\u6ca1\u95ee\u9898\uff0c\u5f88\u597d", 
 "num_cut": 1, 
 "cut_num_for_each_component": [1], 
 "parent_remained_weight": 6572, 
 "adjustable": "yes", 
 "group": "(0, 1)", 
 "parent_number": "MZ23081100033", 
 "material_type": "GD54D+ZF", 
 "coil_number": "C0XR49_1A", 
 "parent_thickness": 0.7, 
 "parent_width": 1205, 
 "parent_length": "C", 
 "parent_weight": 9585, 
 "mill": "TAGAL", 
 "coating": 1, 
 "warehouse": "MJJ", 
 "bundle_number": "1", 
 "components_customer": ["\u5e7f\u5dde\u65b0\u7a0b"], 
 "components_recipient": ["\u65b0\u7a0b\u5e7f\u5dde\u9f99\u7965"], 
 "customers_component_number": ["4112061CDE0100"], 
 "components_thickness": [0.7], 
 "components_width": [1200], 
 "components_length": [1210], 
 "components_delivery_time": ["2024-01-23"], 
 "components_number": ["PZ23071000025"], 
 "components_name": ["\u5de6\u540e\u8f6e\u7f69\u5916\u677f"], 
 "components_output_quantity": [375.9992179216268]}