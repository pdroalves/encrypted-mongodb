from pymongo import MongoClient
import timeit

client = MongoClient()
db = client.benchmark

def load_stored_functions(db):
    # 
    # MongoDB's Stored functions
    # 
    db.system_js.sha256 = """function a(b){function c(a,b){return a>>>b|a<<32-b}for(var d,e,f=Math.pow,g=f(2,32),h="length",i="",j=[],k=8*b[h],l=a.h=a.h||[],m=a.k=a.k||[],n=m[h],o={},p=2;64>n;p++)if(!o[p]){for(d=0;313>d;d+=p)o[d]=p;l[n]=f(p,.5)*g|0,m[n++]=f(p,1/3)*g|0}for(b+="\\x80";b[h]%64-56;)b+="\\x00";for(d=0;d<b[h];d++){if(e=b.charCodeAt(d),e>>8)return;j[d>>2]|=e<<(3-d)%4*8}for(j[j[h]]=k/g|0,j[j[h]]=k,e=0;e<j[h];){var q=j.slice(e,e+=16),r=l;for(l=l.slice(0,8),d=0;64>d;d++){var s=q[d-15],t=q[d-2],u=l[0],v=l[4],w=l[7]+(c(v,6)^c(v,11)^c(v,25))+(v&l[5]^~v&l[6])+m[d]+(q[d]=16>d?q[d]:q[d-16]+(c(s,7)^c(s,18)^s>>>3)+q[d-7]+(c(t,17)^c(t,19)^t>>>10)|0),x=(c(u,2)^c(u,13)^c(u,22))+(u&l[1]^u&l[2]^l[1]&l[2]);l=[w+x|0].concat(l),l[4]=l[4]+w|0}for(d=0;8>d;d++)l[d]=l[d]+r[d]|0}for(d=0;8>d;d++)for(e=3;e+1;e--){var y=l[d]>>8*e&255;i+=(16>y?0:"")+y.toString(16)}return i};"""
    print "Hash de 'batata': %s " % db.system_js.sha256("batata")

    db.system_js.mod1_low = """function a(s, b){
            // Break "s" into 4-digit segments
            var a = s.split("").reverse().join("").match(/.{1,2}/g);
            var size = a.length;
            // Reverse each segment
            for(var i=0; i < size; i++){
                a[i] = parseInt(a[i].split("").reverse().join(""),16);
            }
            var w = 0;// 32 bits
            var r; //16 bits
            for( var i = size - 1; i >= 0; i--){
                // a[i] is a 16 bits word
                w = (w << 16) | (a[i])
                r = parseInt(w/b)*(w >= b);
                w -= r*b*(w >= b);
            }

            return w;
        }"""

    db.system_js.orecompare ="""function a(ctL, ctR) {
            var kl = ctL[0];
            var h = ctL[1];
            var r = ctR[0];
            var v = ctR.splice(1);
            var H = mod1_low(sha256(kl + r),3);
            return (((v[h] - H) % 3) + 3) % 3; 
        }"""


    db.system_js.walk =  """function a(ctL) {
       // Finds the root
    var node = db.customIndex.findOne({root:"1"});

    do{
        if ( node == null)
            return null;
        // Iterates through the tree
        cmp = orecompare(ctL, node.ctR);
        if(cmp == 1)
        // Greater than
        node = db.customIndex.findOne({_id:node.right});
        else if(cmp == 2)
        // Lower than
        node = db.customIndex.findOne({_id:node.left});

    } while ( node != null && cmp != 0);

        return node;
    }"""

load_stored_functions(db)

def sha256():
    return db.system_js.sha256('batata')
def mod1_low():
    return db.system_js.mod1_low('f4610aa514477222afac2b77f971d069780ca2846f375849f3dfa3c0047ebbd1', 3)
def orecompare():
    return db.system_js.orecompare('batata')
def walk():
    return db.system_js.walk('8hsR+II5VxMTehLi43EDWiMYlD2NB9vm+q0yxpne5bA=', 37)

number = 1000
print mod1_low()
def benchmark(db):
    diff = timeit.timeit("sha256()",setup="from __main__ import sha256",number=number)
    print "sha256: %f ms" % (diff/number*1000)
    diff = timeit.timeit("mod1_low()",setup="from __main__ import mod1_low",number=number)
    print "mod1_low: %f ms" % (diff/number*1000)
    # diff = timeit.timeit("orecompare()",setup="from __main__ import orecompare",number=number)
    # print "orecompare: %f ms" % (diff/number*1000)
    # diff = timeit.timeit("walk()",setup="from __main__ import walk",number=number)
    # print "walk: %f ms" % (diff/number*1000)

benchmark(db)