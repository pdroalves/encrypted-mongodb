use test_ore

db.system.js.save({
    _id: "sha256",
    value: function a(b) {
        function c(a,b){return a>>>b|a<<32-b}for(var d,e,f=Math.pow,g=f(2,32),h="length",i="",j=[],k=8*b[h],l=a.h=a.h||[],m=a.k=a.k||[],n=m[h],o={},p=2;64>n;p++)if(!o[p]){for(d=0;313>d;d+=p)o[d]=p;l[n]=f(p,.5)*g|0,m[n++]=f(p,1/3)*g|0}for(b+="\x80";b[h]%64-56;)b+="\x00";for(d=0;d<b[h];d++){if(e=b.charCodeAt(d),e>>8)return;j[d>>2]|=e<<(3-d)%4*8}for(j[j[h]]=k/g|0,j[j[h]]=k,e=0;e<j[h];){var q=j.slice(e,e+=16),r=l;for(l=l.slice(0,8),d=0;64>d;d++){var s=q[d-15],t=q[d-2],u=l[0],v=l[4],w=l[7]+(c(v,6)^c(v,11)^c(v,25))+(v&l[5]^~v&l[6])+m[d]+(q[d]=16>d?q[d]:q[d-16]+(c(s,7)^c(s,18)^s>>>3)+q[d-7]+(c(t,17)^c(t,19)^t>>>10)|0),x=(c(u,2)^c(u,13)^c(u,22))+(u&l[1]^u&l[2]^l[1]&l[2]);l=[w+x|0].concat(l),l[4]=l[4]+w|0}for(d=0;8>d;d++)l[d]=l[d]+r[d]|0}for(d=0;8>d;d++)for(e=3;e+1;e--){var y=l[d]>>8*e&255;i+=(16>y?0:"")+y.toString(16)}return i;
    }
})


db.system.js.save({
    _id: "mod1_low",
    value: function a(s, b){
            // Break "s" into 4-digit segments
            var a = s.split("").reverse().join("").match(/.{1,2}/g);
            var size = a.length;
            // Reverse each segment
            for(var i=0; i < size; i++){
                a[i] = parseInt(a[i].split("").reverse().join(""),16);
            }
            //print("a: " + a);
            var w = 0;// 32 bits
            var r; //16 bits
            for( var i = size - 1; i >= 0; i--){
                //print("word: " + a[i]);
                // a[i] is a 16 bits word
                w = (w << 16) | (a[i])
                //print("w: " + w);
                r = parseInt(w/b)*(w >= b);
                //print("r: " + r);
                w -= r*b*(w >= b);
                //print("w: " + w);
                //print("");
            }

            return w;
        }
})


db.system.js.save({
    _id: "orecompare",
    value: function a(ctL, ctR) {
        var kl = ctL[0];
        var h = ctL[1];
        var r = ctR[0];
        var v = ctR.splice(1);
        var H = mod1_low(sha256(kl + r),3);
        return (((v[h] - H) % 3) + 3) % 3; 
    }
})


db.system.js.save({
    _id: "walk",
    value: function a(ctL) {
    // Finds the root
    var node = db.customIndex.findOne({root:"1"});
    print("node: " + node._id);

    do{
        if ( node == null)
            return null;
        // Iterates through the tree
        cmp = orecompare(ctL, node.ctR);
        print("node: " + node._id);
        print("cmp: " + cmp);
        if(cmp == 1)
        // Greater than
        node = db.customIndex.findOne({_id:node.right});
        else if(cmp == 2)
        // Lower than
        node = db.customIndex.findOne({_id:node.left});

    } while ( node != null && cmp != 0);

        return node;
    }
})

db.eval(function(){return mod1_low("f682d9337965d28f7dd90359a9a5a2ae952c125856da81883c090d51e7829bd7",3)});
db.eval(function(){return sha256("Ee3jBtLZjDkkjKSFtgYRXd1IVQIOduGTaqXveuWreJk=" + "8c222b900f598a0eda3f29ac48cdf3fab6d43c28f66dfd43ba4e5999b106fec2326185a6df087dbf8dc161ab8d3a9204b59e771d037c48856f641b2b61006fb7933977aa75b23147a3ab85c98c6ca0a9d11236af6287905a68655a1ab5ed2550502096c7fdf21dddece1e15c09091c5d1aecf1007ffb321bc9dc1ffd5a0aefa1")})
db.eval(function(){
    // var node = db.customIndex.findOne({root:"1"}); 
    var node = db.customIndex.findOne({_id:ObjectId("57f331767c18c5099855d2c0")}); 
    return orecompare(['ELvsmx+rDCJtDg3AahhtZQNdn6mM9RZtJVsDu5KUodQ=', 1], node.ctR);
})
db.eval(function(){return walk(['ELvsmx+rDCJtDg3AahhtZQNdn6mM9RZtJVsDu5KUodQ=', 1])})

