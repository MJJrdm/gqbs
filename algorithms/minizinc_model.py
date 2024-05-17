from minizinc import Model

def create_model():
    only_order_plan_model = Model()
    only_order_plan_model.add_string(
        """
        int: num_components; 
        array[1..num_components] of int: components_width;
        int: parent_width;
        int: min_waste;
        array[1..num_components] of var int: cut;
        var int: left = parent_width - sum(i in 1..num_components) (cut[i] * components_width[i]);
        var 0..1: only_one;

        constraint forall(i in 1..num_components) (cut[i] >= 0);
        constraint cut[1] >= 1;
        constraint sum(i in 1..num_components) (cut[i]) <= 8;
        constraint only_one = if sum(i in 1..num_components)(cut[i]) = 1 then 1 else 0 endif;
        constraint left >= (1 - only_one) * min_waste;
        var int: obj2 = sum(i in 1..num_components) (cut[i]);
        """
    )
    
    return only_order_plan_model


def create_storage_recommendation_model():
    recommendation_model = Model()
    recommendation_model.add_string(
        """
        int: num_components;
        int: weight_requirement;
        int: buffer;
        array[1..num_components] of int: components_weights;
        array[1..num_components] of var 0..1: used;
        var int: output_weight = sum(i in 1..num_components) (used[i] * components_weights[i]);

        constraint output_weight >= (weight_requirement - buffer);
        """
    )
    
    return recommendation_model
    