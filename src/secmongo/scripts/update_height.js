function(name, index_name){
    var left, right, new_node, parent;
    var collection = db.getCollection(name);
    parent = collection.findOne({parent: null, iname: index_name});
    while(parent != null){
        left_height = get_height(collection.findOne({_id: parent['left']}));
        right_height = get_height(collection.findOne({_id: parent['right']}));
        collection.updateOne({_id: parent['_id']}, {$set: {height: 1 + Math.max(left_height, right_height)}});
        parent = collection.findOne({_id: parent['parent']});
    }
}