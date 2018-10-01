'''
Created on 10. 7. 2018

@author: horinek
'''

import os 
print os.path.dirname(os.path.realpath(__file__))

f = open("../Release/vario2.eep", "rb")
data = f.read()
f.close()

f = open("../src/defaults.h", "w")
f.write("#define DEFAULT_CFG_LENGTH    %d\n" % len(data))
f.write("const uint8_t default_cfg[] PROGMEM = {\n");

i = 0
for c in data:
    f.write("0x%02X, " % ord(c))
    i += 1
    if i > 16:
        i = 0
        f.write("\n")
        
f.write("};\n")
    
print "done"
    