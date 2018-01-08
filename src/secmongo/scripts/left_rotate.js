function(collection, node){
    var right, parent;
    right = collection.findOne({_id: node["right"]});
    // Set original left child's right child parent to node.
    if(right['left'] != null) {
        collection.updateOne(
            {_id: right['left']},
            {$set: {parent: node['_id']}}
        );
    }

    // Set original parent child to right child of node.
    if(node["parent"] != null) {
        parent = collection.findOne({_id: node["parent"]});
        if(parent['left'] != null){
            side = ((node['_id'].equals(parent['left'])) ? 'left' : 'right');
        }else{
            side = 'right'
        }
        if(side == 'left') {
            collection.updateOne(
                {_id: parent['_id']},
                {$set: {left: right['_id']}}
            );
        } else {
            collection.updateOne(
                {_id: parent['_id']},
                {$set: {right: right['_id']}}
            );
        }
    }

    // Set node's right child to right's original right child update parent
    // of node to original right child.
    collection.updateOne(
        {_id: node['_id']},
        {$set: {right: right['left'], parent: right['_id'],
            height: 1 + Math.max(
                get_height(collection.findOne({_id: node['left']})),
                get_height(collection.findOne({_id: right['left']}))
            )}
        }
    );
    // Set orginal right's parent to node's original parent.
    collection.updateOne(
        {_id: right['_id']},
        {$set: {parent: node['parent'], left: node['_id'],
            height: 1 + Math.max(
                get_height(collection.findOne({_id: node['_id']})),
                get_height(collection.findOne({_id: right['right']}))
            )}
        }
    );
}