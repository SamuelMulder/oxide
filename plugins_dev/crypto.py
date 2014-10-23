"""
Copyright (c) 2014 Sandia Corporation. 
Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation, 
the U.S. Government retains certain rights in this software.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import api
import re

def crypto(args, opts):
    """
Plugin: Looks for cryptographic methods inside binary files
Synatax: 
        crypto %oid --<cryptographic functions>|show
        
        Example:
            
            crypto %oid --sha1 --sha256 --aes



    """
    args, invalid = api.valid_oids(args)
    if not args:
        raise ShellSyntaxError("Must provide an oid")
    args = api.expand_oids(args)
    allData = {}
    if not opts:
        opts['sha1'] = ""
        opts['sha256'] = ""
        opts['aes'] = ""
    
    for oid in args:
        src = api.source(oid)
        file_data = api.get_field(src, oid, "data") 
        
        asm = api.retrieve('function_extract', [oid])
        if not asm: continue
        #print asm
        retVal = {}
        if 'sha1' in opts:
            sha1Percent = findSha1(asm,file_data,retVal)
            retVal['SHA1']['Percent']=sha1Percent*100
        if 'sha256'in opts:
            sha256Percent = findSha256(asm,file_data,retVal)
            retVal['SHA256']['Percent']=sha256Percent*100
        if 'aes' in opts:
            aesPercent = findAES(asm,file_data,retVal)
            retVal['AES']['Percent']=aesPercent*100
        allData[oid] = retVal
    return allData
    
   
exports = [crypto]    




def findSha1(functions,file_data,retVal):
    
    retVal['SHA1'] = {}
    #print "---------------------SHA-1--------------------------"
    counter = [0 for x in xrange(7)]
    
    inits = findExtInitSha1(file_data)
    constants = findExtConstSha1(file_data)

    if inits:
        retVal['SHA1']['External Initializations'] = inits
        #print "External Initializations"    
        #print inits
        counter[0] = 1
    if constants:
        retVal['SHA1']['External Constants'] = constants
        #print "External Constants"
        #print constants
        counter[1] = 1
    for func in functions:
        pre = findPreSha1V1(functions[func],functions)
        round0 = findRound0Sha1V1(functions[func],functions)
        round1 = findRound1Sha1V1(functions[func],functions)
        round2 = findRound2Sha1V1(functions[func],functions)
        round3 = findRound3Sha1V1(functions[func],functions)
        constants = findConstSha1(functions[func],functions)
        inits = findInitSha1(functions[func],functions)
        
        if constants:
            if func not in retVal['SHA1']:
                retVal['SHA1'][func]=[]
            retVal['SHA1'][func].append("Constants")
            #print "Constants"
            #print constants  
            counter[0] = 1
        if inits:
            if func not in retVal['SHA1']:
                retVal['SHA1'][func]=[]
            retVal['SHA1'][func].append("Initializations")
            #print "Initializations"
            #print inits  
            counter[1] = 1  
        if pre:
            if func not in retVal['SHA1']:
                retVal['SHA1'][func]=[]
            retVal['SHA1'][func].append("Pre-Processing")
            #print "Pre--"
            #print pre
            counter[2] = 1
        if round0:
            if func not in retVal['SHA1']:
                retVal['SHA1'][func]=[]
            retVal['SHA1'][func].append("Round 0")
            #print "Round 0"
            #print round0
            counter[3] = 1
        if round1:
            if func not in retVal['SHA1']:
                retVal['SHA1'][func]=[]
            retVal['SHA1'][func].append("Round 1")
            #print "Round 1"
            #print round1
            counter[4] = 1
        if round2:
            if func not in retVal['SHA1']:
                retVal['SHA1'][func]=[]
            retVal['SHA1'][func].append("Round 2")
            #print "Round 2"
            #print round2
            counter[5] = 1
        if round3:
            if func not in retVal['SHA1']:
                retVal['SHA1'][func]=[]
            retVal['SHA1'][func].append("Round 3")
            #print "Round 3"
            #print round3
            counter[6] = 1
    #raw_input("done 1")
    count = 0
    for x in counter:
        count+=x
    return count/7.0

def findSha256(functions,file_data,retVal):  
    #print "---------------------SHA-256--------------------------"  
    retVal['SHA256'] = {}

    counter = [0 for x in xrange(5)]
    inits = findExtInitSha256(file_data)
    
    if inits:
        retVal['SHA256']['External Initializations'] = inits
        #print "External Initializations"    
        #print inits
        counter[0]=1

    for func in functions:
        pre = findPreSha256(functions[func],functions)
        rounds = findRoundSha256(functions[func],functions)
        bigSigma = findBigSigmaSha256(functions[func],functions)
        smallSigma = findSmallSigmaSha256(functions[func],functions)
        inits = findInitsSha256(functions[func],functions)
        if inits:
            if func not in retVal['SHA256']:
                retVal['SHA256'][func]=[]
            retVal['SHA256'][func].append("Initializations")
            counter[0]=1
        if pre:
            if func not in retVal['SHA256']:
                retVal['SHA256'][func]=[]
            retVal['SHA256'][func].append("Pre-Processing")
            #print "Pre--"
            #print pre
            counter[1]=1
        if rounds:
            if func not in retVal['SHA256']:
                retVal['SHA256'][func]=[]
            retVal['SHA256'][func].append("Rounds")
            #print "Rounds"
            #print rounds
            counter[2]=1
        if bigSigma:
            if func not in retVal['SHA256']:
                retVal['SHA256'][func]=[]
            retVal['SHA256'][func].append("Big Sigmas")
            #print "Rotates"
            #print rot
            counter[3]=1
        if smallSigma:
            if func not in retVal['SHA256']:
                retVal['SHA256'][func]=[]
            retVal['SHA256'][func].append("Small Sigmas")
            #print "Rotates"
            #print rot
            counter[4]=1
    #raw_input("done 256")
    count = 0
    for x in counter:
        count+=x
    return count/5.0
    
def findAES(functions,file_data,retVal):
    #print "---------------------AES--------------------------" 
    retVal['AES'] = {}
    sbox = findSbox(file_data)
    invsbox = findInvSbox(file_data) 
    counter = [0 for x in xrange(6)]
    if sbox:
        retVal['AES']['SBox'] = sbox
        #print "SBox"
        #print sbox
        counter[0] = 1
    if invsbox:
        retVal['AES']['Inverse SBox'] = invsbox
        #print "Inverse SBox"
        #print invsbox
        counter[1] = 1
    for func in functions:
        addkey4 = findAddRoundKey4(functions[func],functions)
        addkey6 = findAddRoundKey6(functions[func],functions)
        addkey8 = findAddRoundKey8(functions[func],functions)
        subBytes = findSubBytes(functions[func],functions)
         
        if addkey4 and not addkey6:
            if func not in retVal['AES']:
                retVal['AES'][func]=[]
            retVal['AES'][func].append("Add Round Key 128-bit key")
            #print "Add Round Key 4"
            #print addkey4
            counter[2]=1
        if addkey6 and not addkey8:
            if func not in retVal['AES']:
                retVal['AES'][func]=[]
            retVal['AES'][func].append("Add Round Key 192-bit key")
            #print "Add Round Key 6"
            #print addkey6
            counter[3]=1
        if addkey8 :
            if func not in retVal['AES']:
                retVal['AES'][func]=[]
            retVal['AES'][func].append("Add Round Key 256-bit key")
            #print "Add Round Key 8"
            #print addkey8
            counter[4]=1
        if subBytes:
            if func not in retVal['AES']:
                retVal['AES'][func]=[]
            retVal['AES'][func].append("SubByte")
            #print "Sub Bytes"
            #print subBytes
            counter[5]=1
    #raw_input("done AES")
    count = 0
    for x in counter:
        count+=x
    return count/6.0

def toHex(obj):
    ret = ''
    for c in obj:
        m = hex(ord(c))[2:]
        if len(m)==1:
            m = '0'+m
        ret+=m
    return ret


def findSbox(file_data):
    h = toHex(file_data)
    find = [m.start() for m in re.finditer('637c777bf26b6fc53001672bfed7ab76ca82c97dfa5947f0add4a2af9ca472c0b7fd9326363ff7cc',h)]
    if find: 
        return str(int(find[0])/2)
    
def findInvSbox(file_data):
    h = toHex(file_data)
    find = [m.start() for m in re.finditer('52096ad53036a538bf40a39e81f3d7fb',h)]
    if find:
        return str(int(find[0])/2)

def findAddRoundKey4(func,functions):
    log = getLogic(func)
    
    foundKey=False 
    for i in xrange(len(log)-3):
        if log[i]['mnem']=="xor" and log[i+1]['mnem']=="xor" and log[i+2]['mnem']=="xor" and log[i+3]['mnem']=="xor":
            foundKey=True
            break  
    if foundKey:
        return func['insns'][0]['addr']
    return None
  
def findAddRoundKey6(func,functions):
    log = getLogic(func)
    
    foundKey=False 
    for i in xrange(len(log)-5):
        if log[i]['mnem']=="xor" and log[i+1]['mnem']=="xor" and log[i+2]['mnem']=="xor" and log[i+3]['mnem']=="xor"and log[i+4]['mnem']=="xor" and log[i+5]['mnem']=="xor":
            foundKey=True
            break

    if foundKey:
        return func['insns'][0]['addr']
    return None
        
def findAddRoundKey8(func,functions):
    log = getLogic(func)
    
    foundKey=False 
    for i in xrange(len(log)-7):
        if log[i]['mnem']=="xor" and log[i+1]['mnem']=="xor" and log[i+2]['mnem']=="xor" and log[i+3]['mnem']=="xor"and log[i+4]['mnem']=="xor" and log[i+5]['mnem']=="xor"and log[i+6]['mnem']=="xor" and log[i+7]['mnem']=="xor":
            foundKey=True
            break

    if foundKey:
        return func['insns'][0]['addr']  
    return None    
        
def findSubBytes(func,functions):
    log = getLogic(func)
    
    foundSub1=False
    foundSub2=False
    foundSub3=False
    foundSub4=False
    loc = 0
    for i in xrange(len(log)-2):
        if log[i]['mnem']=="shr" and log[i+1]['mnem']=='and'  and log[i+2]['mnem']=='or':
            foundSub1=True
            loc=i+1
            break    

    for i in xrange(loc,len(log)-2):
        if log[i]['mnem']=="shr" and log[i+1]['mnem']=='and'  and log[i+2]['mnem']=='or':
            foundSub2=True
            loc=i+1
            break 

    for i in xrange(loc,len(log)-2):
        if log[i]['mnem']=="shr" and log[i+1]['mnem']=='and'  and log[i+2]['mnem']=='or':
            foundSub3=True
            loc=i+1
            break
             
    for i in xrange(loc,len(log)-1):
        if log[i+1]['mnem']=='and' :
            foundSub4=True
            loc=i+1
            break
    #if foundSub1 or foundSub2 or foundSub3 or foundSub4:
        #print foundSub1, foundSub2, foundSub3, foundSub4
        #print func['insns'][0]['addr']  
    if foundSub1 and foundSub2 and foundSub3 and foundSub4:
        return func['insns'][0]['addr']
    return None


def findExtInitSha256(file_data):
    f1=False
    f2=False
    f3=False
    f4=False
    f5 = False
    f6 = False
    f7 = False
    f8 = False
    locs = [0,0,0,0,0,0,0,0]
    h = toHex(file_data)
    find = [m.start() for m in re.finditer('6a09e667',h)]
    if find: 
        f1=True
        locs[0]=int(find[0])/2  
    find = [m.start() for m in re.finditer('bb67ae85',h)]
    if find: 
        f2=True 
        locs[1]=int(find[1])/2       
    find = [m.start() for m in re.finditer('3c6ef372',h)]
    if find: 
        f3=True  
        locs[2]=int(find[2])/2 
    find = [m.start() for m in re.finditer('a54ff53a',h)]
    if find: 
        f4=True 
        locs[3]=int(find[3])/2      
    find = [m.start() for m in re.finditer('510e527f',h)]
    if find: 
        f5=True 
        locs[4]=int(find[4])/2        
    find = [m.start() for m in re.finditer('9b05688c',h)]
    if find: 
        f6=True  
        locs[5]=int(find[5])/2 
    find = [m.start() for m in re.finditer('1f83d9ab',h)]
    if find: 
        f7=True 
        locs[6]=int(find[6])/2      
    find = [m.start() for m in re.finditer('5be0cd19',h)]
    if find: 
        f8=True 
        locs[7]=int(find[7])/2       

    if f1 and f2 and f3 and f4 and f5 and f6 and f7 and f8:
        return locs

    
    

def findInitsSha256(func,file_data):    

    f1=False
    f2=False
    f3=False
    f4=False
    f5=False
    f6=False
    f7=False
    f8=False
    

    loc = [0 for x in xrange(8)]
    for i in xrange(len(func['insns'])):    
        if 's_ops' in func['insns'][i]:
            for x in func['insns'][i]['s_ops']:
                if type(x['data'])==type({}):
                    try:
                        if x['data']['disp']==1779033703:
                            f1=True 
                            loc[0]=func['insns'][i]['addr']                   
                        if x['data']['disp']==3144134277:
                            f2=True 
                            loc[1]=func['insns'][i]['addr']
                        if x['data']['disp']==1013904242:
                            f3=True 
                            loc[2]=func['insns'][i]['addr']
                        if x['data']['disp']==2773480762:
                            f4=True 
                            loc[3]=func['insns'][i]['addr']
                        if x['data']['disp']==1359893119:
                            f5=True 
                            loc[4]=func['insns'][i]['addr']                   
                        if x['data']['disp']==2600822924:
                            f6=True 
                            loc[5]=func['insns'][i]['addr']
                        if x['data']['disp']==528734635:
                            f7=True 
                            loc[6]=func['insns'][i]['addr']
                        if x['data']['disp']==1541459225:
                            f8=True 
                            loc[7]=func['insns'][i]['addr']
                    except:
                        continue
                try:
                    if x['data']==1779033703:
                        f1=True 
                        loc[0]=func['insns'][i]['addr']                      
                    if int('0x100000000',16)+x['data']==3144134277:
                        f2=True 
                        loc[1]=func['insns'][i]['addr']
                    if x['data']==1013904242:
                        f3=True 
                        loc[2]=func['insns'][i]['addr']
                    if int('0x100000000',16)+x['data']==2773480762:
                        f4=True 
                        loc[3]=func['insns'][i]['addr']
                    if x['data']==1359893119:
                        f5=True 
                        loc[4]=func['insns'][i]['addr']                      
                    if int('0x100000000',16)+x['data']==2600822924:
                        f6=True 
                        loc[5]=func['insns'][i]['addr']
                    if x['data']==528734635:
                        f7=True 
                        loc[6]=func['insns'][i]['addr']
                    if x['data']==1541459225:
                        f8=True 
                        loc[7]=func['insns'][i]['addr']
                except:
                    continue
    #print loc
    if f1 and f2 and f3 and f4 and f5 and f6 and f7 and f8:
        return func['insns'][0]['addr']

def findPreSha256(func,functions):
    log = getLogic(func)

    foundSh1=False
    foundSh2=False
    
    foundRot1=False
    foundRot2=False
    foundRot3=False
    foundRot4=False
    
   
    #raw_input(strLog)
    for i in xrange(len(log)):
        if log[i]['mnem']=="shr" and log[i]['s_ops'][0]['data']==3:
            foundSh1=True
            break
    for i in xrange(len(log)):
        if log[i]['mnem']=="shr" and log[i]['s_ops'][0]['data']==10:
            foundSh2=True
            break
    foundRot1 = findRotate(log,17)
    foundRot2 = findRotate(log,19)
    foundRot3 = findRotate(log,7)
    foundRot4 = findRotate(log,18)

    
    if not log:
        return None
   
    if foundSh1 and foundSh2 and foundRot1 and foundRot2 and foundRot3 and foundRot4:
        return func['insns'][0]['addr']
    
    return None
    
def findRotate(log,right):
    for i in xrange(len(log)):
        if log[i]['mnem']=='ror' and log[i]['s_ops'][0]['data']==right:
            return True
        if log[i]['mnem']=='rol' and log[i]['s_ops'][0]['data']==32-right:
            return True
        if i+2<len(log):
            if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==right and log[i+1]['mnem']=='shl'and log[i+1]['s_ops'][0]['data']==32-right and log[i+2]['mnem']=='or':
                return True
            if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==32-right and log[i+1]['mnem']=='shr'and log[i+1]['s_ops'][0]['data']==right and log[i+2]['mnem']=='or':
                return True        
    return False


def findRoundSha256(func,functions):
    log = getLogic(func)

    foundCH=False
    foundMaj=False
    


    for i in xrange(len(log)-3):
        if log[i]['mnem']=="and" and log[i+1]['mnem']=="not" and log[i+2]['mnem']=="and" and log[i+3]['mnem']=="xor":
            XorLoc=i
            foundCH=True
            break
        if log[i]['mnem']=="not" and log[i+1]['mnem']=="and" and log[i+2]['mnem']=="and" and log[i+3]['mnem']=="xor":
            XorLoc=i
            foundCH=True
            break
    for i in xrange(len(log)-3):
        if log[i]['mnem']=="and" and log[i+1]['mnem']=="and" and log[i+2]['mnem']=="and" and log[i+3]['mnem']=="xor" and log[i+3]['mnem']=="xor":
            XorLoc=i
            foundMaj=True
            break
        if log[i]['mnem']=="not" and log[i+1]['mnem']=="and" and log[i+2]['mnem']=="xor" and log[i+3]['mnem']=="and"and log[i+3]['mnem']=="xor":
            XorLoc=i
            foundMaj=True
            break
    if foundMaj and foundCH:       
        return func['insns'][0]['addr']
    return None
   
def findBigSigmaSha256(func,functions):

    log = getLogic(func)

    foundRot1=False
    foundRot2=False
    foundRot3=False
    foundRot4=False
    foundRot5=False
    foundRot6=False

    foundRot1 = findRotate(log,2)
    foundRot2 = findRotate(log,13)
    foundRot3 = findRotate(log,22)
    foundRot4 = findRotate(log,6)
    foundRot5 = findRotate(log,11)
    foundRot6 = findRotate(log,25) 
    

    if foundRot1 and foundRot2 and foundRot3 and foundRot4 and foundRot5 and foundRot6:       
        return func['insns'][0]['addr']
    return None


def findSmallSigmaSha256(func,functions):

    log = getLogic(func)

    foundRot1=False
    foundRot2=False
    foundRot3=False
    foundRot4=False
    foundRot5=False
    foundRot6=False

    foundRot1 = findRotate(log,7)
    foundRot2 = findRotate(log,18)
    for f in log:
        if f['mnem']=='shr' and f['s_ops'][0]['data']==3:
            foundRot3=True
    
    foundRot4 = findRotate(log,17)
    foundRot5 = findRotate(log,19) 
    for f in log:
        if f['mnem']=='shr' and f['s_ops'][0]['data']==10:
            foundRot6=True
    

    if foundRot1 and foundRot2 and foundRot3 and foundRot4 and foundRot5 and foundRot6:       
        return func['insns'][0]['addr']
    return None




def findExtConstSha1(file_data):
    f1=False
    f2=False
    f3=False
    f4=False
    locs = [0,0,0,0]
    h = toHex(file_data)
    find = [m.start() for m in re.finditer('5a827999',h)]
    if find: 
        f1=True
        locs[0]=int(find[0])/2  
    find = [m.start() for m in re.finditer('6ed9eba1',h)]
    if find: 
        f2=True 
        locs[1]=int(find[1])/2       
    find = [m.start() for m in re.finditer('8f1bbcdc',h)]
    if find: 
        f3=True  
        locs[2]=int(find[2])/2 
    find = [m.start() for m in re.finditer('ca62c1d6',h)]
    if find: 
        f4=True 
        locs[3]=int(find[3])/2       
    
    if f1 and f2 and f3 and f4:
        return locs
    
def findExtInitSha1(file_data):
    f1=False
    f2=False
    f3=False
    f4=False
    f5 = False
    locs = [0,0,0,0,0]
    h = toHex(file_data)
    find = [m.start() for m in re.finditer('67452301',h)]
    if find: 
        f1=True
        locs[0]=int(find[0])/2  
    find = [m.start() for m in re.finditer('efcdab89',h)]
    if find: 
        f2=True 
        locs[1]=int(find[1])/2       
    find = [m.start() for m in re.finditer('98badcfe',h)]
    if find: 
        f3=True  
        locs[2]=int(find[2])/2 
    find = [m.start() for m in re.finditer('10325476',h)]
    if find: 
        f4=True 
        locs[3]=int(find[3])/2      
    find = [m.start() for m in re.finditer('c3d2e1f0',h)]
    if find: 
        f5=True 
        locs[4]=int(find[4])/2       

    
    if f1 and f2 and f3 and f4 and f5:
        return locs
    
    

def findConstSha1(func,file_data):    

    f1=False
    f2=False
    f3=False
    f4=False
    

    for i in xrange(len(func['insns'])):    
        if 's_ops' in func['insns'][i]:
            for x in func['insns'][i]['s_ops']:
                if type(x['data'])==type({}):
                    try:
                        if x['data']['disp']==1518500249:
                            f1=True 
                            loc[0]=func['insns'][i]['addr']                   
                        if x['data']['disp']==1859775393:
                            f2=True 
                            loc[1]=func['insns'][i]['addr']
                        if x['data']['disp']==2400959708:
                            f3=True 
                            loc[2]=func['insns'][i]['addr']
                        if x['data']['disp']==3395469782:
                            f4=True 
                            loc[3]=func['insns'][i]['addr']
                    except:
                        continue
                try:
                    if x['data']==1518500249:
                        f1=True 
                        loc[0]=func['insns'][i]['addr']                      
                    if int('0x100000000',16)+x['data']==1859775393:
                        f2=True 
                        loc[1]=func['insns'][i]['addr']
                    if int('0x100000000',16)+x['data']==2400959708:
                        f3=True 
                        loc[2]=func['insns'][i]['addr']
                    if int('0x100000000',16)+x['data']==3395469782:
                        f4=True 
                        loc[3]=func['insns'][i]['addr']
                except:
                    continue
    if f1 and f2 and f3 and f4:
        return func['insns'][0]['addr']
        
def findInitSha1(func,file_data):

    f1=False
    f2=False
    f3=False
    f4=False
    f5=False
    
    
    for i in xrange(len(func['insns'])):
        
        if 's_ops' in func['insns'][i]:
            for x in func['insns'][i]['s_ops']:
                if type(x['data'])==type({}):
                    try:
                        if x['data']['disp']==1732584193:
                            f1=True
                        if int('0x100000000',16)+x['data']['disp']==4023233417:
                            f2=True
                        if int('0x100000000',16)+x['data']['disp']==2562383102:
                            f3=True
                        if x['data']['disp']==271733878:
                            f4=True                  
                        if int('0x100000000',16)+x['data']['disp']==3285377520:
                            f5=True
                    except:
                        continue
                try:
                    if x['data']==1732584193:
                        f1=True
                    if int('0x100000000',16)+x['data']==4023233417:
                        f2=True
                    if int('0x100000000',16)+x['data']==2562383102:
                        f3=True
                    if x['data']==271733878:
                        f4=True                  
                    if int('0x100000000',16)+x['data']==3285377520:
                        f5=True
                except:
                    continue
    if f1 and f2 and f3 and f4 and f5:
        return func['insns'][0]['addr']       
                        
def findPreSha1V1(func,functions):
    #print func
    log = getLogic(func)
    #print func['start']
    #print log
    if not log:
        return None

    XorLoc = 0
    foundXor=False
    foundRol=False
    foundXorLoop=False
    for i in xrange(XorLoc,len(log)-3):
        if log[i]['mnem']=="xor" and log[i+1]['mnem']=="xor" and log[i+2]['mnem']=="xor":
            XorLoc=i+2
            foundXor=True
            break
    for i in xrange(XorLoc,len(log)):
        if log[i]['mnem']=='rol'and log[i]['s_ops'][0]['data']==1:
            foundRol=True
        if log[i]['mnem']=='ror'and log[i]['s_ops'][0]['data']==31:
            foundRol=True
        if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==1:
            foundRol=True
        if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==31:
            foundRol=True
    if  foundXor and foundRol:
        #print log
        return func['insns'][0]['addr']
    return None

def findRound0Sha1V1(func,functions):
#print func
    log = getLogic(func)
    #print func['start']
    #print log
    if not log:
        return None

    XorLoc = 0
    foundXor=False
    foundRol1=False
    foundRol2=False
    foundXorLoop=False
    for i in xrange(0 ,len(log)):
        if log[i]['mnem']=='rol'and log[i]['s_ops'][0]['data']==5:
            foundRol1=True
            XorLoc+=i            
            break
        if log[i]['mnem']=='ror'and log[i]['s_ops'][0]['data']==27:
            foundRol1=True
            XorLoc+=i           
            break
        if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==5:
            foundRol1=True
            XorLoc+=i           
            break
        if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==27:
            foundRol1=True
            XorLoc+=i            
            break
    for i in xrange(0,len(log)-3):
       
        if log[i]['mnem']=="and" and log[i+1]['mnem']=="not" and log[i+2]['mnem']=="and" and log[i+3]['mnem']=="or":
            XorLoc=i
            foundXor=True
            break
        if log[i]['mnem']=="not" and log[i+1]['mnem']=="and" and log[i+2]['mnem']=="and" and log[i+3]['mnem']=="or":
            XorLoc=i
            foundXor=True
            break
        if log[i]['mnem']=="xor" and log[i+1]['mnem']=="and" and log[i+2]['mnem']=="xor":
            XorLoc=i
            foundXor=True
            break
    for i in xrange(0,len(log)):
        if log[i]['mnem']=='rol'and log[i]['s_ops'][0]['data']==30:
            foundRol2=True
        if log[i]['mnem']=='ror'and log[i]['s_ops'][0]['data']==2:
            foundRol2=True
        if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==30:
            foundRol2=True
        if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==2:
            foundRol2=True

    if  foundXor and foundRol1 and foundRol2:
        #print log
        return func['insns'][0]['addr']
    return None

def findRound1Sha1V1(func,functions):
    log = getLogic(func)
    #print func['start']
    #print log
    if not log:
        return None

    XorLoc = 0
    foundXor=False
    foundRol1=False
    foundRol2=False
    foundXorLoop=False
    for i in xrange(XorLoc,len(log)):
        if log[i]['mnem']=='rol'and log[i]['s_ops'][0]['data']==5:
            XorLoc=i
            foundRol1=True
            break
        if log[i]['mnem']=='ror'and log[i]['s_ops'][0]['data']==27:
            XorLoc=i
            foundRol1=True
            break
        if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==5:
            XorLoc=i
            foundRol1=True
            break
        if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==27:
            XorLoc=i
            foundRol1=True
            break
    for i in xrange(0,len(log)-3):
        if log[i]['mnem']=="xor" and log[i+1]['mnem']=="xor":
            XorLoc=i
            foundXor=True
            break
    for i in xrange(0,len(log)):
        if log[i]['mnem']=='rol'and log[i]['s_ops'][0]['data']==30:
            foundRol2=True
        if log[i]['mnem']=='ror'and log[i]['s_ops'][0]['data']==2:
            foundRol2=True
        if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==30:
            foundRol2=True
        if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==2:
            foundRol2=True
    if  foundXor and foundRol1 and foundRol2:
        #print log
        return func['insns'][0]['addr']
    return None

def findRound2Sha1V1(func,functions):
    log = getLogic(func)
    #print func['start']
    #print log
    if not log:
        return None

    XorLoc = 0
    foundXor=False
    foundRol1=False
    foundRol2=False
    foundXorLoop=False
    for i in xrange(XorLoc,len(log)):
        if log[i]['mnem']=='rol'and log[i]['s_ops'][0]['data']==5:
            XorLoc=i
            foundRol1=True
            break
        if log[i]['mnem']=='ror'and log[i]['s_ops'][0]['data']==27:
            XorLoc=i
            foundRol1=True
            break
        if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==5:
            XorLoc=i
            foundRol1=True
            break
        if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==27:
            XorLoc=i
            foundRol1=True
            break
    for i in xrange(0,len(log)-3):
        if log[i]['mnem']=="and" and log[i+1]['mnem']=="and" and log[i+2]['mnem']=="and" and log[i+3]['mnem']=="or"and log[i+4]['mnem']=="or":
            XorLoc=i
            foundXor=True
            break
        if log[i]['mnem']=="and" and log[i+1]['mnem']=="and" and log[i+2]['mnem']=="or" and log[i+3]['mnem']=="and"and log[i+4]['mnem']=="or":
            XorLoc=i
            foundXor=True
            break
        if log[i]['mnem']=="or" and log[i+1]['mnem']=="and" and log[i+2]['mnem']=="and" and log[i+3]['mnem']=="or":
            XorLoc=i
            foundXor=True
            break
    for i in xrange(0,len(log)):
        if log[i]['mnem']=='rol'and log[i]['s_ops'][0]['data']==30:
            foundRol2=True
        if log[i]['mnem']=='ror'and log[i]['s_ops'][0]['data']==2:
            foundRol2=True
        if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==30:
            foundRol2=True
        if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==2:
            foundRol2=True

    if  foundXor and foundRol1 and foundRol2:
        #print log
        return func['insns'][0]['addr']
    return None



def findRound3Sha1V1(func,functions):
    log = getLogic(func)
    #print func['start']
    #print log
    if not log:
        return None

    XorLoc = 0
    foundXor=False
    foundRol1=False
    foundRol2=False
    foundXorLoop=False
    for i in xrange(XorLoc,len(log)):
        if log[i]['mnem']=='rol'and log[i]['s_ops'][0]['data']==5:
            XorLoc=i
            foundRol1=True
            break
        if log[i]['mnem']=='ror'and log[i]['s_ops'][0]['data']==27:
            XorLoc=i
            foundRol1=True
            break
        if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==5:
            XorLoc=i
            foundRol1=True
            break
        if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==27:
            XorLoc=i
            foundRol1=True
            break
    for i in xrange(0,len(log)-3):
        if log[i]['mnem']=="xor" and log[i+1]['mnem']=="xor":
            XorLoc=i
            foundXor=True
            break
    for i in xrange(0,len(log)):
        if log[i]['mnem']=='rol'and log[i]['s_ops'][0]['data']==30:
            foundRol2=True
        if log[i]['mnem']=='ror'and log[i]['s_ops'][0]['data']==2:
            foundRol2=True
        if log[i]['mnem']=='shl'and log[i]['s_ops'][0]['data']==30:
            foundRol2=True
        if log[i]['mnem']=='shr'and log[i]['s_ops'][0]['data']==2:
            foundRol2=True
    if  foundXor and foundRol1 and foundRol2:
        #print log
        return func['insns'][0]['addr']
    return False

def getLogic(insns):
    ret = []
    for isn in insns['insns']:
        
        if isn['mnem'] and(isn['mnem']=='not' or isn['mnem']=='and' or isn['mnem']=='or' or isn['mnem']=='xor' or isn['mnem']=='shl' or isn['mnem']=='shr' or \
                isn['mnem']=='ror' or  isn['mnem']=='rol' or isn['mnem'][0]=='j' or isn['mnem']=='call' or isn['mnem']=='inc' or isn['mnem']=='dec'):
            if isn['mnem']=='and' and isn['s_ops'][0]['data']==0:
                continue
            if isn['mnem']=='xor' and type(isn['s_ops'][0])==type(dict()):            
                #print isn
                #print isn['s_ops'][0]['data'],isn['d_op']['data']
                if isn['s_ops'][0]['data']==isn['d_op']['data']:
                    #print "i got here"
                    continue
            ret.append(isn)
    return ret

