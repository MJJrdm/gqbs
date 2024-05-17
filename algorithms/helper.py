def give_plan_structure_dict(**kwargs):
    plan_dict = {
                'parent_coil_number': '/', 
                'parent_bundle_number': '/',
                'parent_used_weight_in_kg': '/',
                'components': ['/'],
                'components_output_weight': ['/'],
                'cut_info': '/',
                'note': '/',
                'num_cut': '/',
                'cut_num_for_each_component': ['/'],
                'parent_remained_weight': '/'
                }
    plan_dict.update(kwargs)
    return plan_dict

    