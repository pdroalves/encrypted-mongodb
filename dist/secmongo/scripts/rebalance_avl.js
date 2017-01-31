function(name, node_id){
    db.getCollection(name).findOne({_id: node_id},{})
}