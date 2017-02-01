function(collection, node){
    var left, parent;
    left = collection.findOne({_id: node['left']});
    // Set original right child's left child parent to node.
    if(left['right'] != null) {
        collection.updateOne(
            {_id: left['right']},
            {$set: {parent: node['_id']}}
        );
    }

    // Set original parent child to left child of node.
    if(node['parent'] != null){
        parent = collection.findOne({_id: node['parent']});
        if(parent['left'] != null){
            side = ((node['_id'].equals(parent['left'])) ? 'left' : 'right');
        }else{
            side = 'right'
        }
        if(side == 'left') {
            collection.updateOne(
                {_id: parent['_id']},
                {$set: {left: left['_id']}}
            );
        }else {
            collection.updateOne(
                {_id: parent['_id']},
                {$set: {right: left['_id']}}
            );
        }
    }

    // Set node's left child to left's original right child update parent
    // of node to original right child.
    collection.updateOne(
        {_id: node['_id']},
        {$set: {
            left: left['right'], parent: left['_id'],
            height: 1 + Math.max(
                get_height(collection.findOne({_id: left['right']})),
                get_height(collection.findOne({_id: node['right']}))
            )}
        }
    );
    // Set orginal left's parent to node's original parent.
    collection.updateOne(
        {_id: left['_id']},
        {$set: {
            parent: node['parent'], right: node['_id'],
            height: 1 + Math.max(
                get_height(collection.findOne({_id: left['left']})),
                get_height(collection.findOne({_id: node['_id']}))
            )}
        }
    );

}