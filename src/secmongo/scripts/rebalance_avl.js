function(name, node_id){
    var new_node, node, balance, left, right;
    var collection = db.getCollection(name);
    new_node = collection.findOne({_id: node_id});
    node = collection.findOne({_id: new_node['parent']});
    var type = "";
    while(node != null){
        left = collection.findOne({_id: node['left']});
        right = collection.findOne({_id: node['right']});
        balance = check_balance(left, right);
        if(balance < -1){
            if(check_balance(collection.findOne({_id: left['left']}),
                             collection.findOne({_id: left['right']})) > 0){
                left_rotate(collection, left);
                node = collection.findOne({"_id": node["_id"]});
            }
            right_rotate(collection, node);
            return;
        } else if(balance > 1){
            if(check_balance(collection.findOne({_id: right['left']}),
                             collection.findOne({_id: right['right']})) < 0){
                right_rotate(collection, right);
                node = collection.findOne({"_id": node["_id"]});
                type += "right"
            }
            left_rotate(collection, node);
            return;
        }
        node = collection.findOne({_id: node['parent']});
    }
}